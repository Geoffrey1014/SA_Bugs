#include "stdio.h"
#include <stdbool.h>
#include <stdint.h>

void clang_analyzer_eval(int) {}

uint16_t a() {
  for (;;)
    if (a() <= 0) {
      clang_analyzer_eval((a() <= 0) == true);
      clang_analyzer_eval(((a()) < (0)) || ((a()) == (0)));
      clang_analyzer_eval(((a()) + 0) <= ((0) + 0));
      clang_analyzer_eval(((a()) + 0) <= ((0) + 1));
      clang_analyzer_eval(((a()) + 1) <= ((0) + 1));
      clang_analyzer_eval(((a()) + 0) <= ((0) + 2));
      clang_analyzer_eval(((a()) + 1) <= ((0) + 2));
      clang_analyzer_eval(((a()) + 2) <= ((0) + 2));
      clang_analyzer_eval(((a()) - 0) <= ((0) - 0));
      clang_analyzer_eval((!(a() <= 0)) == false);
      clang_analyzer_eval((((a()) >= (0)) && ((a()) != (0))) == false);
      clang_analyzer_eval(true);
      ;
    }
  return 2;
}