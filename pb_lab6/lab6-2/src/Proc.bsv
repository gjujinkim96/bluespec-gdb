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

typedef struct {
  RIndx rd;
  Data  data;
} ForwardData deriving(Bits, Eq);

function Data forward(Maybe#(ForwardData) mem, Maybe#(ForwardData) exe, Data orig, RIndx rs);
  ForwardData h1 = fromMaybe(?, mem);
  ForwardData h2 = fromMaybe(?, exe);
  Bit#(2) forwardA = 0;
  Data ret = orig;

  if (isValid(exe) && isValid(mem)) begin
    if (h2.rd == rs)
      forwardA = 2;
    else if (h1.rd == rs)
      forwardA = 1;
  end
  else if (isValid(exe)) begin
    if (h2.rd == rs)
      forwardA = 2;
  end
  else if (isValid(mem)) begin
    if (h1.rd == rs)
      forwardA = 1;
  end

  case (forwardA)
    1: ret = h1.data;
    2: ret = h2.data;
  endcase

  return ret;
endfunction

(*synthesize*)
module mkProc(Proc);
  Reg#(Addr)    pc  <- mkRegU;
  RFile         rf  <- mkBypassRFile; // wr < rd :  Refer to p.20, M10
  //RFile         rf  <- mkRFile;
  IMemory     iMem  <- mkIMemory;
  DMemory     dMem  <- mkDMemory;
  CsrFile     csrf <- mkCsrFile;

  // Control hazard handling Elements : 2 Epoch registers and one BypassFifo
  Reg#(Bool) fEpoch <- mkRegU;
  Reg#(Bool) eEpoch <- mkRegU;
  Fifo#(1, Addr) execRedirect <- mkBypassFifo;

  // Data hazard handling Elements
  Fifo#(1, Fetch2Decode) stallFetch <- mkBypassFifo;
  Fifo#(1, RIndx) ldHazard <- mkBypassFifo;
  Fifo#(1, ForwardData) exeHazard <- mkBypassFifo;
  Fifo#(1, ForwardData) memHazard <- mkBypassFifo;
   
  // Fetch stage -> Rest stage PipelineFifo
  Fifo#(1, Maybe#(Fetch2Decode))  f2d <- mkPipelineFifo;
  Fifo#(1, Maybe#(Decode2Exec))  d2e <- mkPipelineFifo;
  Fifo#(1, Maybe#(ExecInst)) e2m <- mkPipelineFifo;
  Fifo#(1, Maybe#(ExecInst)) m2w <- mkPipelineFifo;

 /* TODO:  Lab 6-2: Implement a 5-stage pipelined processor using a bypassing method. 
           Define the proper bypassing units using BypassFiFo */
  rule doFetch(csrf.started);
   	let inst = iMem.req(pc);
   	let ppc = pc + 4;
    $display("Fetch from pc : %d", pc);

    if(execRedirect.notEmpty) begin
      execRedirect.deq;
      pc <= execRedirect.first;
      fEpoch <= !fEpoch;
      f2d.enq(Invalid);
    end
    else if (stallFetch.notEmpty) begin
      let x = stallFetch.first;
      f2d.enq(Valid(x));
      stallFetch.deq;
    end
    else begin
      pc <= ppc;
      f2d.enq(Valid(Fetch2Decode{inst:inst, pc:pc, ppc:ppc, epoch:fEpoch})); 
    end
  endrule

  rule doDecode(csrf.started);
    let x = f2d.first;
    f2d.deq;
    $display("Decode");

    Maybe#(RIndx) h = Invalid;
    if (ldHazard.notEmpty) begin
      h = Valid(ldHazard.first);
      ldHazard.deq;
    end

    if (isValid(x)) begin
      let y = validValue(x);
      let inst   = y.inst;
      let pc   = y.pc;
      let ppc    = y.ppc;
      let iEpoch = y.epoch;

      // Decode
      let dInst = decode(inst);

      // Determine Load-Use hazard
      Bool stall = False;
      if (isValid(h)) begin
        let rd = validValue(h);
        let rs1 = isValid(dInst.src1) ? validValue(dInst.src1) : ?;
        let rs2 = isValid(dInst.src2) ? validValue(dInst.src2) : ?;
        if (rd == rs1 || rd == rs2)
          stall = True;
      end

      if (!stall) begin
        // Register Read
        let rVal1 = isValid(dInst.src1) ? rf.rd1(validValue(dInst.src1)) : ?;
        let rVal2 = isValid(dInst.src2) ? rf.rd2(validValue(dInst.src2)) : ?;
        let csrVal = isValid(dInst.csr) ? csrf.rd(validValue(dInst.csr)) : ?;
        d2e.enq(Valid(Decode2Exec{dInst:dInst, pc:pc, ppc:ppc, epoch:iEpoch, rVal1:rVal1, rVal2:rVal2, csrVal:csrVal}));
      end
      else begin
        d2e.enq(Invalid);
        if (!execRedirect.notEmpty)
          stallFetch.enq(y);
      end
    end

    else begin
      d2e.enq(Invalid);
    end

  endrule

  rule doExecute(csrf.started);
    let x = d2e.first;
    d2e.deq;
    $display("Execute");

    Maybe#(ForwardData) h1 = Invalid;
    Maybe#(ForwardData) h2 = Invalid;
    if (memHazard.notEmpty) begin
      h1 = Valid(memHazard.first);
      memHazard.deq;
    end
    if (exeHazard.notEmpty) begin
      h2 = Valid(exeHazard.first);
      exeHazard.deq;
    end

    if (isValid(x)) begin
      let y = validValue(x);
      let iEpoch = y.epoch;
      
      if(iEpoch == eEpoch) begin
        let dInst = y.dInst;
        let pc = y.pc;
        let ppc = y.ppc;
        let csrVal = y.csrVal;

        // Forwarding
        let rVal1 = isValid(dInst.src1) ? forward(h1, h2, y.rVal1, validValue(dInst.src1)) : ?;
        let rVal2 = isValid(dInst.src2) ? forward(h1, h2, y.rVal2, validValue(dInst.src2)) : ?;

        // Execute         
        let eInst = exec(dInst, rVal1, rVal2, pc, ppc, csrVal);               
        
        // Forward Data for potential Load-Use Hazard
        if (eInst.iType == Ld) begin
          ldHazard.enq(validValue(eInst.dst));
        end

        if(eInst.mispredict) begin
          eEpoch <= !eEpoch;
          execRedirect.enq(eInst.addr);
        end

        e2m.enq(Valid(eInst));
      end
      else begin
        e2m.enq(Invalid);
      end
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
      let eInst = validValue(x);
      let iType = eInst.iType;

      // Forward Data for potential data hazard
      if (isValid(eInst.dst)) begin
        let rd = validValue(eInst.dst);
        if (rd != 0)
          exeHazard.enq(ForwardData{rd:rd, data:eInst.data});
      end

      // Memory
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
    $display("WriteBack");

    if (isValid(x)) begin
      let eInst = validValue(x);

      // Forward Data & WriteBack
      if (isValid(eInst.dst)) begin
        let rd = validValue(eInst.dst);
        if (rd != 0)
          memHazard.enq(ForwardData{rd:rd, data:eInst.data});
        rf.wr(rd, eInst.data);
      end
      csrf.wr(eInst.iType == Csrw ? eInst.csr : Invalid, eInst.data);
    end
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
