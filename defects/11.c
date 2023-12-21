#include <stdio.h>

void a(int *e) { *e = (0 == e); }

int main() {
  int d[4];
  for (int c = 0; c < 4; c++)
    ;
  a(d);
  return 0;
}