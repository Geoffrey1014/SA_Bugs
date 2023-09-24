#include <stdio.h>
int main() {   
  int e = 1;
  int *f;

  for (int i = 0; i < 1; i++) {
    e = 0;
    __analyzer_eval(0 == e);
  }
  
  __analyzer_eval(0 == e);
  f = e;

  __analyzer_eval(0 == f);
  *f = 1;

  return 0;
}