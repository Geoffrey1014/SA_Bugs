#include <stdio.h>

int l;

int *b(int *n) {
  for (; l < 3;)
    return n;
}

int d() {
  int f;
  int *g = &f;
  int *i;
  (i = b(g)) || 1;
  ;
  *i;
}

int main() { d(); }
