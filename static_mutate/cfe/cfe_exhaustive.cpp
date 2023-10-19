#include <sstream>

#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"

#include "cfe_branch_visitor.hpp"

using namespace clang;
using namespace clang::tooling;

static llvm::cl::OptionCategory ExhaustiveCategory("Exhaustive transformer");


void InitTool() {
    FlagPreFix.addCategory(ExhaustiveCategory);
    Stub.addCategory(ExhaustiveCategory);
    FuncWrap.addCategory(ExhaustiveCategory);
    with_arg_str(
            with_desc(
                    TargetBranch,
                    "target branch to insert error label, 0 for do nothing"),
            "exhaustive-target").addCategory(ExhaustiveCategory);
}

class ExhaustiveTransformer : public BranchVisitor<ExhaustiveTransformer, true> {
private:
    bool has_return_wrap_decl = false;

    std::string GenStubAndInsertStubDeclAtMainStart(BrCount insert_branch_stub, bool semi = true) {
        std::stringstream stub_stream;
        stub_stream << FlagPreFix.getValue() << insert_branch_stub;

        R.InsertVarDeclAtBegin("int", stub_stream.str(), "0");

        stub_stream << "++";
        if (semi) stub_stream << ';';

        return stub_stream.str();
    }

public:
    void TraverseSuccess() override {
        if (TargetBranch.getValue() > branch_count)
            caut_errs() << "branch target invalid.\n";
        else if (TargetBranch.getValue() > 0) {
            R.overwriteChangedFiles();
        }
    }

public:
    bool TraverseReturnStmt(ReturnStmt *S, DataRecursionQueue *Queue = nullptr) {
        if (at_main) {
            auto Return = dyn_cast<ReturnStmt>(S);
            if (!has_return_wrap_decl) {
                R.InsertAtBegin("int " + FuncWrap.getValue() + "(int i){ _stub(); return i; };");
                has_return_wrap_decl = true;
            }
            R.InsertTextBefore(Return->getRetValue()->getBeginLoc(), FuncWrap.getValue() + "(");
            R.InsertTextAfterToken(Return->getEndLoc(), ")");
        }
        return RecursiveASTVisitor::TraverseReturnStmt(S, Queue);
    }

    bool HandleWithBranch(BrCount br, Stmt *S) override {
        if (TargetBranch.getValue() == br) {
            if (auto Compound = dyn_cast<CompoundStmt>(S)) {
                R.InsertTextAfterToken(Compound->getLBracLoc(), GenStubAndInsertStubDeclAtMainStart(br));
            } else {
                caut_errs() << "branch target is not compound stmt.\n";
                return false;
            }
        }
        return true;
    }

    bool HandleWithBranch(BrCount br, Expr *E) override {
        if (TargetBranch.getValue() == br) {
            R.InsertTextBefore(E->getBeginLoc(), "( " + GenStubAndInsertStubDeclAtMainStart(br, false) + ", ");
            R.InsertTextAfterToken(E->getEndLoc(), " )");
        }
        return true;
    }

    bool TraverseCallExpr(CallExpr *Call, DataRecursionQueue *Queue = nullptr) {
        if (auto *Func = dyn_cast<FunctionDecl>(Call->getCalleeDecl())) {
            if (!Func->getDeclName().isIdentifier())
                return BranchVisitor::TraverseCallExpr(Call, Queue);

            std::vector<std::string>::iterator t;
            std::string func_name = Func->getName().str();
            SourceLocation lParen, rParen = Call->getRParenLoc(), semiLoc;
            // if call stmt is used in expr or other format, skip
            if (!stmtSemi(Call, R, semiLoc)) {
                return RecursiveASTVisitor::TraverseCallExpr(Call, Queue);
            } else if (!nextToken(Call->getBeginLoc(), R, tok::TokenKind::l_paren, lParen)) {
                return RecursiveASTVisitor::TraverseCallExpr(Call, Queue);
            }
            unsigned argc = Call->getNumArgs();
#define CHECK_ARGC(required_argc, func_name) if (argc != required_argc) { \
caut_errs() << func_name << " function requires " << required_argc << " args, got " << argc << "\n"; \
return false; \
}
            std::string prep_rep, postp_rep;
            if (find(exit_points, func_name, t)) {
                // exit(i_exp) => stub(); if ((i_exp) != 0) err()
                CHECK_ARGC(1, "exit")
                prep_rep = STUB_FUNC_CALL_STMT(Stub) + " if ( ";
                postp_rep = std::string(" != 0) ") + STUB_FUNC_CALL(ErrStub);
            } else if (find(abort_points, func_name, t)) {
                // abort() => stub(); err()
                CHECK_ARGC(0, "abort")
                prep_rep = STUB_FUNC_CALL_STMT(Stub) + ' ' + ErrStub.getValue();
            } else if (find(assert_points, func_name, t)) {
                // __assert_fail("","",0,"") => stub(); err()
                // it's impossible to handle assert MACRO.
                CHECK_ARGC(4, "assert")
                R.ReplaceText(SourceRange(Call->getBeginLoc(), Call->getEndLoc()),
                              STUB_FUNC_CALL_STMT(Stub) + STUB_FUNC_CALL(ErrStub));
            }

            if (!prep_rep.empty())
                R.ReplaceText(Call->getBeginLoc(), func_name.length(), prep_rep);
            if (!postp_rep.empty())
                R.InsertTextAfterToken(rParen, postp_rep);
        }
        return RecursiveASTVisitor::TraverseCallExpr(Call, Queue);
    }
};

int main(int argc, const char **argv) {
    InitTool();

    auto OptionsParser = CommonOptionsParser::create(argc, argv, ExhaustiveCategory);

    ClangTool Tool(OptionsParser->getCompilations(),
                   OptionsParser->getSourcePathList());

    return Tool.run(newFrontendActionFactory<TransformAction<ExhaustiveTransformer>>().get());
}
