// RUN: %clang_analyze_cc1 %s \
// RUN:   -analyzer-checker=core \
// RUN:   -analyzer-checker=debug.ExprInspection \
// RUN:   -verify

void clang_analyzer_printState();
void clang_analyzer_eval(int);
void clang_analyzer_warnIfReached();

void foo(int x, int y) {
  int *a = 0;
  
  if (x * y != 0) // x * y == 0
    return;

  if (x % 3 == 0) // x % 3 != 0 -> x != 0
    return;
  
  if (y != 1)     // y == 1     -> x == 0
    return;

//   clang_analyzer_eval(x != 0);
//   *a = 1;
  clang_analyzer_warnIfReached(); // no-warning
}
