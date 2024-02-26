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
} Fetch2Rest deriving(Bits, Eq);

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
  
  // Fetch stage -> Rest stage PipelineFifo
  Fifo#(1, Fetch2Rest)  f2r <- mkPipelineFifo;

  // Scoreboard declaration. Use this module to deal with the data hazard problem. Refer to scoreboard.bsv in common-lib directory 
  Scoreboard#(4) sb <- mkPipelineScoreboard;


/* TODO: Lab 6-1: Implement a 5-stage pipelined processor using given a scoreboard. 
   Scoreboard is already implemented. Refer to common-lib/scoreboard.bsv and PPT materials. 
   Use the interface of the scoreboard.bsv properly */
  rule doFetch(csrf.started);
   	let inst = iMem.req(pc);
   	let ppc = pc + 4;

    if(execRedirect.notEmpty) begin
      execRedirect.deq;
      pc <= execRedirect.first;
      fEpoch <= !fEpoch;
    end
    else begin
      pc <= ppc;
    end

    f2r.enq(Fetch2Rest{inst:inst, pc:pc, ppc:ppc, epoch:fEpoch}); 
  endrule

  rule doRest(csrf.started);
    let inst   = f2r.first.inst;
    let pc   = f2r.first.pc;
    let ppc    = f2r.first.ppc;
    let iEpoch = f2r.first.epoch;
    f2r.deq;

    if(iEpoch == eEpoch) begin
      	// Decode 
   	    let dInst = decode(inst);

        // Register Read 
        let rVal1 = isValid(dInst.src1) ? rf.rd1(validValue(dInst.src1)) : ?;
        let rVal2 = isValid(dInst.src2) ? rf.rd2(validValue(dInst.src2)) : ?;
        let csrVal = isValid(dInst.csr) ? csrf.rd(validValue(dInst.csr)) : ?;

    		// Execute         
        let eInst = exec(dInst, rVal1, rVal2, pc, ppc, csrVal);               
        
        if(eInst.mispredict) begin
          eEpoch <= !eEpoch;
          execRedirect.enq(eInst.addr);
        end

      //Memory 
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

      //WriteBack 
      if (isValid(eInst.dst)) begin
          rf.wr(fromMaybe(?, eInst.dst), eInst.data);
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
