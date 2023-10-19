#ifndef CFE_TOOLING_CFE_UTILS_H
#define CFE_TOOLING_CFE_UTILS_H

#include <cfloat>
#include <cmath>
#include <sstream>

#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Lex/Token.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/ADT/Optional.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "llvm/Support/raw_ostream.h"

class CfeRewriter : public clang::Rewriter {
public:
    bool InsertText(clang::SourceLocation Loc, llvm::StringRef Str, bool InsertAfter, bool indentNewLines) {
        if (getSourceMgr().getFileID(Loc) == getSourceMgr().getMainFileID())
            return Rewriter::InsertText(Loc, Str, InsertAfter, indentNewLines);
        else
            return true;
    }

    void InsertAtBegin(const std::string &text) {
        auto l = getSourceMgr().getLocForStartOfFile(getSourceMgr().getMainFileID());
        InsertTextBefore(l, text + "\n");
    }

    void
    InsertVarDeclAtBegin(const std::string &var_type,
                         const std::string &var_name,
                         const std::string &var_init_text) {
        return InsertAtBegin(var_type + " " + var_name + " = " + var_init_text + ";");
    }
};

template<typename T>
class TransformAction : public clang::ASTFrontendAction {
public:
    std::unique_ptr<clang::ASTConsumer> CreateASTConsumer(clang::CompilerInstance &CI,
                                                          llvm::StringRef InFile) override {
        return std::unique_ptr<clang::ASTConsumer>(new T());
    }
};

llvm::raw_ostream &caut_success() {
    return llvm::outs() << "[CAUT success]\n";
}

llvm::raw_ostream &caut_outs(bool new_line = false) {
    return llvm::outs() << (new_line ? "\n[CAUT out] " : "[CAUT out] ");
}

llvm::raw_ostream &caut_errs(bool new_line = false) {
    return llvm::outs() << (new_line ? "\n[CAUT error] " : "[CAUT error] ");
}

void caut_flush() { llvm::outs().flush(); }

inline bool locToken(
        clang::SourceLocation l,
        CfeRewriter const &R,
        clang::tok::TokenKind tok_type,
        clang::SourceLocation &tok_loc) {
    clang::Token t{};
    if (!clang::Lexer::getRawToken(l, t, R.getSourceMgr(), R.getLangOpts())
        && t.getKind() == tok_type) {
        tok_loc = t.getLocation();
        return true;
    }
    return false;
}

bool nextToken(
        clang::SourceLocation l,
        CfeRewriter const &R,
        clang::tok::TokenKind tok_type,
        clang::SourceLocation &out) {
    const llvm::Optional<clang::Token> next = clang::Lexer::findNextToken(
            l,
            R.getSourceMgr(),
            R.getLangOpts()
    );
    if (next && next.value().getKind() == tok_type) {
        out = next.value().getLocation();
        return true;
    } else {
        return false;
    }
}

bool declSemiOrRBrac(clang::DeclaratorDecl *D, CfeRewriter const &R, clang::SourceLocation &out) {
    return nextToken(D->getEndLoc(), R, clang::tok::TokenKind::semi, out) ||
           locToken(D->getEndLoc(), R, clang::tok::TokenKind::r_brace, out);
}

bool stmtSemi(clang::Stmt *Stmt, CfeRewriter const &R, clang::SourceLocation &out) {
    if (auto Null = clang::dyn_cast<clang::NullStmt>(Stmt)) {
        out = Null->getEndLoc();
        return true;
    }
    return nextToken(Stmt->getEndLoc(), R, clang::tok::TokenKind::semi, out);
}

bool declSemi(clang::Decl *Decl, CfeRewriter const &R, clang::SourceLocation &out) {
    return nextToken(Decl->getEndLoc(), R, clang::tok::TokenKind::semi, out);
}

bool stmtSemiOrRBrac(clang::Stmt *Stmt, CfeRewriter const &R, clang::SourceLocation &out) {
    if (stmtSemi(Stmt, R, out)) return true;
    else if (locToken(Stmt->getEndLoc(), R, clang::tok::TokenKind::r_brace, out))
        return true;
    return false;
}

template<typename T>
bool find(std::vector<T> v, T value, typename std::vector<T>::iterator &out) {
    typename std::vector<T>::iterator it = std::find(v.begin(), v.end(), value);
    if (it != v.end()) {
        out = it;
        return true;
    }
    return false;
}

template<typename T>
std::string to_str(T value) {
    std::ostringstream ss;
    ss << value;
    return ss.str();
}

template<typename T>
T next_float(T f) { return std::nextafter(f, DBL_MAX); }

template<typename IT>
std::string str_join(const char *const split, IT begin, IT end, std::function<std::string(IT)> mapper) {
    std::ostringstream out_str;

    for (bool first = true; begin != end; ++begin) {
        if (!first) out_str << split;
        out_str << mapper(begin);
        first = false;
    }

    return out_str.str();
}

std::string str_join(const char *const split, std::vector<std::string> &sv) {
    return str_join<std::vector<std::string>::const_iterator>(split, sv.begin(), sv.end(),
                                                              [](std::vector<std::string>::const_iterator s) { return *s; });
}

bool get_callee_name(clang::CallExpr *Call, clang::StringRef &out) {
    if (auto Callee = Call->getCalleeDecl()) {
        if (auto *Func = clang::dyn_cast<clang::FunctionDecl>(Callee)) {
            out = Func->getName();
            return true;
        }  /* else could not get name of `FunctionDecl` */
    } else {
        /* todo: handle `CallExpr` with no `FunctionCall` */
    }
    return false;
}

bool is_verifier_stub_call(clang::CallExpr *Call, clang::StringRef *callee_name = nullptr) {
    clang::StringRef verifier_callee_name;
    if (!get_callee_name(Call, verifier_callee_name)) return false;
    if (verifier_callee_name.startswith("__VERIFIER_")) {
        // copy
        *callee_name = verifier_callee_name;
        return true;
    }
    return false;
}

bool is_nondet_value(clang::StringRef callee_name, clang::StringRef *stub_type_out = nullptr) {
    if (callee_name.startswith("__VERIFIER_nondet_")) {
        if (stub_type_out != nullptr) *stub_type_out = callee_name.slice(18, callee_name.size());
        return true;
    }
    return false;
}

bool is_nondet_value(clang::CallExpr *Call, clang::StringRef *stub_type_out = nullptr) {
    clang::StringRef callee_name;
    return is_verifier_stub_call(Call, &callee_name) && is_nondet_value(callee_name, stub_type_out);
}

/// Return true if success, otherwise false
bool rewrite_nondet_value(clang::CallExpr *Call, CfeRewriter &R, const std::string &new_text) {
    return !(R.InsertTextBefore(Call->getBeginLoc(), "/* ") ||
             R.InsertTextAfterToken(Call->getEndLoc(),
                                    " */ " + new_text));
}

#endif //CFE_TOOLING_CFE_UTILS_H
