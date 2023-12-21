#include <stdbool.h>

int foo(bool a, bool b) {
  int *c = 0;
  int *d = 0;
  if (a || b) {
    __analyzer_eval(a);
    __analyzer_eval(b);
    __analyzer_eval(a || b);
    __analyzer_eval((a || b) == true);

    if (!a) {
      if (!b) {
        __analyzer_eval(a || b);
        *d = 0;
      }
    }
  }
}