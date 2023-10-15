#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "cfe_branch_visitor.hpp"

using namespace clang;
using namespace clang::tooling;

static llvm::cl::OptionCategory NopCategory("Nop transformer");


class NopTransformer : public BranchVisitor<NopTransformer, true> {
public:
    void TraverseSuccess() override {
        if (TargetBranch.getValue() > branch_count)
            caut_errs() << "branch target invalid.\n";
        else
            caut_errs() << "cfe check success";
    }

    bool HandleWithBranch(BrCount br, Stmt *S) override {
        if (auto Compound = dyn_cast<CompoundStmt>(S)) {
            return true;
        } else {
            caut_errs() << "branch target is not compound stmt.\n";
            return false;
        }
    }

    bool HandleWithBranch(BrCount br, Expr *E) override { return true; }
};

int main(int argc, const char **argv) {
    with_desc(TargetBranch, "target branch to check").addCategory(NopCategory);

    auto OptionsParser = CommonOptionsParser::create(argc, argv, NopCategory);

    ClangTool Tool(OptionsParser->getCompilations(),
                   OptionsParser->getSourcePathList());

    return Tool.run(newFrontendActionFactory<TransformAction<NopTransformer>>().get());
}
