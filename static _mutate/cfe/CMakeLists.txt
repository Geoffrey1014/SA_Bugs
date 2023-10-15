set(LLVM_LINK_COMPONENTS support)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}  -fno-rtti -fvisibility-inlines-hidden ${LLVM_CXXFLAGS}")

set(CFE_BIN_LIST
        cfe_preprocess
        cfe_checksum
        cfe_exhaustive
        cfe_nop
        cfe_branch_replace
        cfe_sv_comp
        cfe_stub_count
        cfe_stub_reduce)

foreach (cfe ${CFE_BIN_LIST})
    add_executable(${cfe} "${cfe}.cpp")

    target_link_libraries(${cfe} 
    PRIVATE
    clangTooling
    clangAST
    clangASTMatchers
    clangBasic
    clangFrontend
    clangSerialization
)
endforeach ()
