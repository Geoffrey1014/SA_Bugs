#include "stdio.h"
#include "stdint.h"

int main() {
int32_t e = 0;
  int32_t *f = &e;
  int16_t g[2][9] = {8};
  if (g[0][1]) {
    int32_t h;
    // printf("h: %d\n", h);
    int32_t **i = &f;
    *i = h; // fp of NPD
  }
  printf("NPD_FLAG\n");
  if (*f)
    printf("223\n"); }