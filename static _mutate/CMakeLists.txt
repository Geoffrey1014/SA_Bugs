set(LLVM_LINK_COMPONENTS support)

add_clang_executable(tooling-sample
  ToolingSample.cpp
  utils.cpp
  )
target_link_libraries(tooling-sample
PRIVATE
clangAST
clangASTMatchers
clangBasic
clangFrontend
clangSerialization
clangTooling
)
