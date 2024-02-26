import Types::*;
import ProcTypes::*;
import CMemTypes::*;
import MemInit::*;
import RFile::*;
import IMemory::*;
import DMemory::*;
import Decode::*;
import Exec::*;
import CsrFile::*;
import Fifo::*;
import Scoreboard::*;
import GetPut::*;

typedef struct {
  Instruction inst;
  Addr pc;
  Addr ppc;
  Bool epoch;
} Fetch2Decode deriving(Bits, Eq);

typedef struct {
  DecodedInst dInst;
  Addr pc;
  Addr ppc;
  Bool epoch;
  Data rVal1;
  Data rVal2;
  Data csrVal;
} Decode2Exec deriving(Bits, Eq);

(*synthesize*)
module mkProc(Proc);
  Reg#(Addr)    pc  <- mkRegU;
  RFile         rf  <- mkBypassRFile;  // Refer to p.20, M10
  //RFile         rf  <- mkRFile;
  IMemory     iMem  <- mkIMemory;
  DMemory     dMem  <- mkDMemory;
  CsrFile     csrf <- mkCsrFile;
  
  // Control hazard handling Elements : 2 Epoch registers and one BypassFifo
  Reg#(Bool) fEpoch <- mkRegU;
  Reg#(Bool) eEpoch <- mkRegU;
  Fifo#(1, Addr) execRedirect <- mkBypassFifo; 
  
  // Data hazard handling
  Fifo#(1, Fetch2Decode) stallpc <- mkBypassFifo;

  // Fetch stage -> Rest stage PipelineFifo
  Fifo#(1, Fetch2Decode)  f2d <- mkPipelineFifo;
  Fifo#(1, Decode2Exec)   d2e <- mkPipelineFifo;
  Fifo#(1, Maybe#(ExecInst)) e2m <- mkPipelineFifo;
  Fifo#(1, Maybe#(ExecInst)) m2w <- mkPipelineFifo;

  // Scoreboard declaration. Use this module to deal with the data hazard problem. Refer to scoreboard.bsv in common-lib directory 
  Scoreboard#(4) sb <- mkPipelineScoreboard;


/* TODO: Lab 6-1: Implement a 5-stage pipelined processor using given a scoreboard. 
   Scoreboard is already implemented. Refer to common-lib/scoreboard.bsv and PPT materials. 
   Use the interface of the scoreboard.bsv properly */
  rule doFetch(csrf.started);
   	let inst = iMem.req(pc);
   	let ppc = pc + 4;

    if (execRedirect.notEmpty) begin
      pc <= execRedirect.first;
      fEpoch <= !fEpoch;
      execRedirect.deq;
    end
    else if (stallpc.notEmpty) begin
      let x = stallpc.first;
      f2d.enq(x);
      stallpc.deq;
      $display("Fetch");
      $display("Fetched from %d", x.pc);
    end
    else begin
      pc <= ppc;
      f2d.enq(Fetch2Decode{inst:inst, pc:pc, ppc:ppc, epoch:fEpoch});
      $display("Fetch");
      $display("Fetched from %d", pc);
    end
  endrule

  rule doDecode(csrf.started);
    let x = f2d.first;
    let inst   = x.inst;
    let pc   = x.pc;
    let ppc    = x.ppc;
    let iEpoch = x.epoch;
    f2d.deq;

    // Decode
    let dInst = decode(inst);
    let stall = sb.search1(dInst.src1) || sb.search2(dInst.src2);
    if (!stall) begin
      // Register Read
      let rVal1 = isValid(dInst.src1) ? rf.rd1(validValue(dInst.src1)) : ?;
      let rVal2 = isValid(dInst.src2) ? rf.rd2(validValue(dInst.src2)) : ?;
      let csrVal = isValid(dInst.csr) ? csrf.rd(validValue(dInst.csr)) : ?;
      d2e.enq(Decode2Exec{dInst:dInst, pc:pc, ppc:ppc, epoch:iEpoch, rVal1:rVal1, rVal2:rVal2, csrVal:csrVal});
      sb.insert(dInst.dst);
      $display("Decode");
    end
    else begin
      if (!execRedirect.notEmpty) begin
        stallpc.enq(x);
        $display("Stall from %d", pc);
      end
      else
        $display("Stall and Mispredicted");
    end
  endrule

  rule doExecute(csrf.started);
    let x = d2e.first;
    let iEpoch = x.epoch;
    d2e.deq;
    $display("Execute");

    if(iEpoch == eEpoch) begin
      let dInst = x.dInst;
      let pc = x.pc;
      let ppc = x.ppc;
      let rVal1 = x.rVal1;
      let rVal2 = x.rVal2;
      let csrVal = x.csrVal;

      // Execute         
      let eInst = exec(dInst, rVal1, rVal2, pc, ppc, csrVal);               
      
      if(eInst.mispredict) begin
        eEpoch <= !eEpoch;
        execRedirect.enq(eInst.addr);
        $display("Mispredict! Fetch from %d", eInst.addr);
      end

      e2m.enq(Valid(eInst));
    end
    else begin
      e2m.enq(Invalid);
    end
  endrule

  rule doMemory(csrf.started);
    let x = e2m.first;
    e2m.deq;
    $display("Memory");

    if (isValid(x)) begin
      //Memory 
      let eInst = validValue(x);
      let iType = eInst.iType;
      case(iType)
        Ld :
        begin
          let d <- dMem.req(MemReq{op: Ld, addr: eInst.addr, data: ?});
          eInst.data = d;
        end
        St:
        begin
          let d <- dMem.req(MemReq{op: St, addr: eInst.addr, data: eInst.data});
        end
        Unsupported :
        begin
          $fwrite(stderr, "ERROR: Executing unsupported instruction\n");
          $finish;
        end
      endcase

      m2w.enq(Valid(eInst));
    end
    else begin
      m2w.enq(Invalid);
    end
  endrule

  rule doWriteBack(csrf.started);
    let x = m2w.first;
    m2w.deq;
    $display("Writeback");

    if (isValid(x)) begin
      //WriteBack 
      let eInst = validValue(x);
      if (isValid(eInst.dst)) begin
          rf.wr(fromMaybe(?, eInst.dst), eInst.data);
      end
      csrf.wr(eInst.iType == Csrw ? eInst.csr : Invalid, eInst.data);
    end
    sb.remove;
  endrule

  method ActionValue#(CpuToHostData) cpuToHost;
    let retV <- csrf.cpuToHost;
    return retV;
  endmethod

  method Action hostToCpu(Bit#(32) startpc) if (!csrf.started);
    csrf.start(0);
    eEpoch <= False;
    fEpoch <= False;
    pc <= startpc;
  endmethod

  interface iMemInit = iMem.init;
  interface dMemInit = dMem.init;

endmodule
