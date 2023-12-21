#include <stdio.h>

int *a(int i) {
  int *n = 0;
  return n;
}

int main() {
  int d; int *e; int **f = &e;
  for (int g = 0; g < 3; g++)
    for (d = 2; d; d--) {
      printf("NPD_FLAG\n");
      *f = a(f == 0);
    }
}