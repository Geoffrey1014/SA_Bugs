//------------------------------------------------------------------------------
// Tooling sample. Demonstrates:
//
// * How to write a simple source tool using libTooling.
// * How to use RecursiveASTVisitor to find interesting AST nodes.
// * How to use the Rewriter API to rewrite the source code.
//
// Eli Bendersky (eliben@gmail.com)
// This code is in the public domain
//------------------------------------------------------------------------------
#include <sstream>
#include <string>

#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Frontend/ASTConsumers.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/raw_ostream.h"
#include "clang/AST/Type.h"
#include "utils.cpp"

using namespace llvm;
using namespace clang;
using namespace clang::driver;
using namespace clang::tooling;



static llvm::cl::OptionCategory ToolingSampleCategory("Analyzer Evaluation Transformer");
static llvm::cl::opt<bool> DumpAst ("ast",
                                          llvm::cl::desc("dump ast"),
                                          llvm::cl::init(false));
static llvm::cl::opt<std::string> Analyzer(cl::Positional, "analyzer",llvm::cl::desc("Specify Static Analyzer"));
// Apply a custom category to all command-line options so that they are the
// only ones displayed.
// static llvm::cl::OptionCategory MyToolCategory("my-tool options");

// CommonOptionsParser declares HelpMessage with a description of the common
// command-line options related to the compilation database and input files.
// It's nice to have this help message in all tools.
// static cl::extrahelp CommonHelp(CommonOptionsParser::HelpMessage);

// A help message for this specific tool can be added afterwards.
// static cl::extrahelp MoreHelp("\nMore help text hwg...\n");


class MutableExprVisitor : public RecursiveASTVisitor<MutableExprVisitor>{
  private:
      CompilerInstance &Instance;
      bool mutableFlag = false;

  public:
  MutableExprVisitor(CompilerInstance &I) :Instance(I) {
// TODO: initialize 
  }

  bool getFlag(){
    return mutableFlag;
  }

  bool VisitCallExpr(Expr *E) {
    ASTContext &context = Instance.getASTContext();
    PrintingPolicy policy = context.getPrintingPolicy();

      std::string exprStr;
      llvm::raw_string_ostream out(exprStr);
      E->printPretty(out,NULL,policy,0U,"\n",&context);
      llvm::errs() << "\nCallExpr: " << exprStr << " \n";

      // mutableFlag = true;
      return true;

  }

  bool VisitCompoundAssignOperator(CompoundAssignOperator * CAo){
    ASTContext &context = Instance.getASTContext();
    PrintingPolicy policy = PrintingPolicy(context.getLangOpts());

    std::string exprStr;
    llvm::raw_string_ostream out(exprStr);
    CAo->printPretty(out, NULL, policy);

    llvm::errs() << "\n CompoundAssignOperator: " << exprStr << " \n";

    clang::CompoundAssignOperator::Opcode opcode = CAo->getOpcode();
    llvm::errs() << "\n CompoundAssign opcode: " <<  opcode << " \n";

    if( opcode <= BinaryOperatorKind::BO_OrAssign){
      mutableFlag = true;
      return false;
    }

    return true;
  }

  bool VisitUnaryOperator(UnaryOperator * Uop){
    ASTContext &context = Instance.getASTContext();
    PrintingPolicy policy = PrintingPolicy(context.getLangOpts());

    std::string exprStr;
    llvm::raw_string_ostream out(exprStr);
    Uop->printPretty(out, NULL, policy);

    llvm::errs() << "\nVisitUnaryOperator: " << exprStr << " \n";

    clang::UnaryOperator::Opcode opcode = Uop->getOpcode();
    llvm::errs() << "\n Unary opcode: " <<  opcode << " \n";

    if( opcode <= UnaryOperatorKind::UO_PreDec){
      mutableFlag = true;
      return false;
    }
    return true;
  }

};

class CastVisitor : public RecursiveASTVisitor<CastVisitor> {
  private:
    QualType type;
    CompilerInstance &Instance;
    ASTContext &context;
    PrintingPolicy policy;

  public:
    CastVisitor(CompilerInstance &I)
        : Instance(I), context(I.getASTContext()), policy(context.getPrintingPolicy()) {}

    bool VisitExpr(Expr *E) {
      std::string exprStr;
      llvm::raw_string_ostream out(exprStr);
      E->printPretty(out,NULL,policy,0U,"\n",&context);
      

      if (isa<ImplicitCastExpr>(E)){
        // llvm::errs() << "\n Visit ImplicitCastExpr: " <<  exprStr << "; class: " << E->getStmtClassName()<< " \n";
        return true;
      }
      else{
        QualType typeE = E->getType();
        // llvm::errs() << "\n Visit Expr: " <<  exprStr << "; class: " << E->getStmtClassName()<< " \n";
        // llvm::errs() << "\n Type: " << typeE << " \n";
        type = typeE;
        return false;
      }
    }
    QualType getType(){
        return type;
      }
};


class ExprVisitor : public RecursiveASTVisitor<ExprVisitor> {
  private:
    std::vector<std::string> &exprEvelVector, &exprEvelVector2, &ifCondVector;
    CompilerInstance &Instance;

  public:
    ExprVisitor(std::vector<std::string> &V,std::vector<std::string> &V2,std::vector<std::string> &Vi, CompilerInstance &I)
        : exprEvelVector(V), exprEvelVector2(V2), ifCondVector(Vi), Instance(I) {}

    bool VisitExpr(Expr *E) {
      ASTContext &context = Instance.getASTContext();
      PrintingPolicy policy = context.getPrintingPolicy();
      std::string exprStr;
      llvm::raw_string_ostream out(exprStr);
      E->printPretty(out,NULL,policy,0U,"\n",&context);

      // exprEvelVector.push_back(exprStr);
      llvm::errs() << "\nVisitExpr: " <<  exprStr << " \n";
      if ( isa<BinaryOperator>(E) )
      {
        // VisitBinaryOperator((BinaryOperator *)E);
        return true;
      }
      else if (isa<ParenExpr>(E)){
        return true;
      }
      else if (isa<CastExpr>(E))
        return true;
      return false;
    }

    bool VisitBinaryOperator(BinaryOperator *B) {
    Expr *lhs = B->getLHS();
    Expr *rhs = B->getRHS();

    ASTContext &context = Instance.getASTContext();
    PrintingPolicy policy = PrintingPolicy(context.getLangOpts());

    std::string exprStr;
    llvm::raw_string_ostream out(exprStr);
    B->printPretty(out, NULL, policy);
    llvm::errs() << "\nVisitBinaryOperator: " << exprStr << " \n";

    llvm::StringRef opCodeStr = B->getOpcodeStr();
    clang::BinaryOperator::Opcode opcode = B->getOpcode();
    llvm::errs() << "\nOpcode: " << opCodeStr << " \n";

    std::string LExprStr;
    llvm::raw_string_ostream outL(LExprStr);
    lhs->printPretty(outL, NULL, policy);
    llvm::errs() << "\nlefthand: " << LExprStr << " \n";

    std::string RExprStr;
    llvm::raw_string_ostream outR(RExprStr);
    rhs->printPretty(outR, NULL, policy);
    llvm::errs() << "\nrighthand: " << RExprStr << " \n";

    QualType typeE = B->getType();
    QualType typeL = lhs->getType();
    QualType typeR = rhs->getType();
    llvm::errs() << "\nExpr Type: " << typeE << " \n";
    llvm::errs() << "\nLeft Hand Side Type: " << typeL << " \n";
    llvm::errs() << "\nLeft Hand Side Type: " << typeR << " \n";

    CastVisitor* cvL = new CastVisitor(Instance);
    CastVisitor* cvR = new CastVisitor(Instance);
    cvL->TraverseStmt(lhs);
    cvR->TraverseStmt(rhs);
    typeL = cvL->getType();
    typeR = cvR->getType();
    delete cvL;
    delete cvR;

    if(!typeL.getTypePtrOrNull()){
      llvm::errs() << "\nFail to get Left Hand Side Original Type \n";
      return true;
    }
    else{
      llvm::errs() << "\nLeft Hand Side Original Type: " << typeL << " \n";
    }
    
    if(!typeR.getTypePtrOrNull()){
      llvm::errs() << "\nFail to get Right Hand Side Original Type \n";
      return true;
    }
    else{
      llvm::errs() << "\nLeft Hand Side Original Type: " << typeR << " \n";
    }
    

    switch (opcode) {
    case BinaryOperatorKind::BO_LAnd:
      bo_and_rules(exprStr, LExprStr, RExprStr, exprEvelVector);
      this->TraverseStmt(lhs);
      this->TraverseStmt(rhs);
      break;
    case BinaryOperatorKind::BO_LOr:
      bo_or_rules(exprStr, LExprStr, RExprStr, exprEvelVector);
      break;
      
    case BinaryOperatorKind::BO_EQ:
      bo_eq_rules(exprStr, LExprStr, typeL, RExprStr, typeR, exprEvelVector, exprEvelVector2, ifCondVector);
      break;

    case BinaryOperatorKind::BO_LT:
      bo_lt_rules(exprStr, LExprStr, typeL, RExprStr, typeR, exprEvelVector, exprEvelVector2, ifCondVector);
      break;

    case BinaryOperatorKind::BO_GT:
     bo_gt_rules(exprStr, LExprStr, typeL, RExprStr, typeR, exprEvelVector, exprEvelVector2, ifCondVector);
      break;
    case BinaryOperatorKind::BO_LE: 
      bo_le_rules(exprStr, LExprStr, typeL, RExprStr, typeR, exprEvelVector, exprEvelVector2, ifCondVector);
      break;

    case BinaryOperatorKind::BO_GE:
      bo_ge_rules(exprStr, LExprStr, typeL, RExprStr, typeR, exprEvelVector, exprEvelVector2, ifCondVector);

      break;
    case BinaryOperatorKind::BO_NE:
      bo_ne_rules(exprStr, LExprStr, RExprStr, exprEvelVector);
      break;

    default:
      break;
    }

    return false;
    }

};

 
// By implementing RecursiveASTVisitor, we can specify which AST nodes
// we're interested in by overriding relevant methods.
class MyASTVisitor : public RecursiveASTVisitor<MyASTVisitor> {
private:
  Rewriter &TheRewriter;
  CompilerInstance &Instance;

public:
  MyASTVisitor(Rewriter &R, CompilerInstance &I)
      : TheRewriter(R), Instance(I) {}

  bool VisitStmt(Stmt *s) {
    // Only care about If statements.
    if (isa<IfStmt>(s)) {
      IfStmt *IfStatement = cast<IfStmt>(s);
      Expr *cond = IfStatement->getCond();
      Stmt *Then = IfStatement->getThen();
      
      //TODO: 处理一下非 CompoundStmt 的情况
      if (!isa<CompoundStmt>(Then))
        return true;

      CompoundStmt *ThenCmps = cast<CompoundStmt>(Then);
      // return when body is empty
      if (ThenCmps->body_empty())
        return true;

      // TODO  处理变量在条件分支中声明的情况
      // VarDecl *v = IfStatement->getConditionVariable();

      MutableExprVisitor * mv = new MutableExprVisitor(Instance);
      mv->TraverseStmt(cond);

      if(mv->getFlag()){
        return true;
      }
      
      // TraverseStmt 
      std::vector<std::string> exprEvelVector, exprEvelVector2, ifCondVector;
      ExprVisitor *v = new ExprVisitor(exprEvelVector, exprEvelVector2, ifCondVector, Instance);
      v->TraverseStmt(cond);
      // v->VisitExpr(cond);

      // get the string of cond
      ASTContext &context = Instance.getASTContext();
      PrintingPolicy policy = context.getPrintingPolicy();
      std::string exprStr;
      llvm::raw_string_ostream out(exprStr);
      cond->printPretty(out, NULL, policy, 0U, "\n", &context);

      // insert analyzer expressions
      Stmt *firstStmt = *(ThenCmps->body_begin());

      llvm::errs() << "\n ifCondVector size " << ifCondVector.size() << "\n";
      llvm::errs() << "\n exprEvelVector2 size " << exprEvelVector2.size() << "\n";
      llvm::errs() << "\n exprEvelVector size " << exprEvelVector.size() << "\n";
      
      for (std::vector<std::string>::iterator it = exprEvelVector.begin();
           it != exprEvelVector.end(); it++) {
        
        llvm::errs() << *it << "\n";

        if(Analyzer.getValue() == "gcc"){
          TheRewriter.InsertText(firstStmt->getBeginLoc(),
                               std::string() + "__analyzer_eval(" + *it + ");\n", true, true);
        }
        else if (Analyzer.getValue() == "clang"){
          TheRewriter.InsertText(firstStmt->getBeginLoc(),
                               std::string() + "clang_analyzer_eval(" + *it + ");\n", true, true);
        }
        
      }
      
      // insert a if stmt
      if (ifCondVector.size()){
        std::string ifConstraints = "if(";
        for (std::vector<std::string>::iterator it = ifCondVector.begin();
            it != ifCondVector.end(); it++) {
          
          llvm::errs() << *it << "\n";
          ifConstraints += *it;
          if (it != (ifCondVector.end() -1) ){
            ifConstraints += " && ";
          }
          
        }
        ifConstraints += " ) {\n";

        for (std::vector<std::string>::iterator it = exprEvelVector2.begin();
            it != exprEvelVector2.end(); it++) {
          llvm::errs() << *it << "\n";

          if(Analyzer.getValue() == "gcc"){
                                ifConstraints += "__analyzer_eval(" + *it + ");\n";
          }
          else if (Analyzer.getValue() == "clang"){
                                ifConstraints += "clang_analyzer_eval(" + *it + ");\n";
          }

        }
        ifConstraints += "}\n";
        TheRewriter.InsertText(firstStmt->getBeginLoc(), ifConstraints, true, true);
      }
    }

    return true;
  }

  bool VisitFunctionDecl(FunctionDecl *f) {
    // Only function definitions (with bodies), not declarations.
    if (f->hasBody()) {
      Stmt *FuncBody = f->getBody();

      // Type name as string
      QualType QT = f->getReturnType();
      std::string TypeStr = QT.getAsString();

      // Function name
      DeclarationName DeclName = f->getNameInfo().getName();
      std::string FuncName = DeclName.getAsString();

      // Add comment before
      std::stringstream SSBefore;
      SSBefore << "// Begin function: " << FuncName << ", returning " << TypeStr
               << "\n";
      SourceLocation ST = f->getSourceRange().getBegin();

      llvm::errs() << SSBefore.str() << "\n";

    }

    return true;
  }
};

// Implementation of the ASTConsumer interface for reading an AST produced
// by the Clang parser.
class MyASTConsumer : public ASTConsumer {
private:
  MyASTVisitor Visitor;

public:
  MyASTConsumer(Rewriter &R, CompilerInstance &I) : Visitor(R, I) {}

  // Override the method that gets called for each parsed top-level
  // declaration.
  bool HandleTopLevelDecl(DeclGroupRef DR) override {
    for (DeclGroupRef::iterator b = DR.begin(), e = DR.end(); b != e; ++b) {
      // Traverse the declaration using our AST visitor.
      
      // llvm::errs() << "** declaration: " << "\n" ;
      Visitor.TraverseDecl(*b);
      if (DumpAst.getValue())
      {
        (*b)->dump();
      }
      
      
    }
    return true;
  }
};

// For each source file provided to the tool, a new FrontendAction is created.
class MyFrontendAction : public ASTFrontendAction {
private:
  Rewriter TheRewriter;

public:
  MyFrontendAction() {}

  bool BeginSourceFileAction(CompilerInstance &CI) override {
    SourceManager &SM = CI.getSourceManager();
    llvm::errs() << "** BeginSourceFileAction for: "
                 << SM.getFileEntryForID(SM.getMainFileID())->getName() << "\n";
    ;
    return true;
  }

  void EndSourceFileAction() override {
    SourceManager &SM = TheRewriter.getSourceMgr();
    llvm::errs() << "** EndSourceFileAction for: "
                 << SM.getFileEntryForID(SM.getMainFileID())->getName() << "\n";

    // Now emit the rewritten buffer.
    TheRewriter.getEditBuffer(SM.getMainFileID()).write(llvm::outs());
  }

  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI,
                                                 StringRef file) override {
    llvm::errs() << "** Creating AST consumer for: " << file << "\n";
    SourceManager &SM = CI.getSourceManager();

    TheRewriter.setSourceMgr(SM, CI.getLangOpts());
    return std::make_unique<MyASTConsumer>(TheRewriter, CI);
  }
};


int main(int argc, const char **argv) {

  Analyzer.addCategory(ToolingSampleCategory);
  DumpAst.addCategory(ToolingSampleCategory);

  llvm::Expected<clang::tooling::CommonOptionsParser> option =
      CommonOptionsParser::create(argc, argv, ToolingSampleCategory);
  
  clang::tooling::ClangTool tool(option->getCompilations(),
                                 option->getSourcePathList());

  return tool.run(newFrontendActionFactory<MyFrontendAction>().get()); 
}
