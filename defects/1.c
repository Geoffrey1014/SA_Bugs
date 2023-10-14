#include <stdio.h>
int main() {   
  int e = 10086;
  int *f = &e;
  int g = 0;
  int *h[2][1];
  h[1][0] = f;
  if (g == (h[1][0])) {
    // printf("if true\n");
    unsigned int *i = 0;
  }
  printf("NPD_FLAG: %d\n ", *f);
  return 0;
}