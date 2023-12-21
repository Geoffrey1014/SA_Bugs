#include "stdint.h"
#include "stdio.h"
#include <stdbool.h>

void __analyzer_describe();
void __analyzer_eval();
void __analyzer_dump();
void __analyzer_dump_state(const char *name, ...);
void __analyzer_dump_region_model();

void foo(int c) {
  int a = c + 2;
  int b = c + 1;
  __analyzer_dump();
  if (a > b) {
    __analyzer_dump();
    __analyzer_eval(a > b);
    __analyzer_eval(b < a);
    __analyzer_eval(b > a);
  }
}