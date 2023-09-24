#include <stdio.h>
int b( int *p) {
  int n=2;
  printf("reach NPD\n");
  *p = n;
  return 1;
}
int main() {
  int g, h;
  for (int i =0;;i++) {
    int j=1;
    int *k[4][10];
    for (g = 0; g < 4; g++)
      for (h = 0; h < 10; h++)
        k[g][h] = &j;
    if (b(k[1][1])){
        k[1][1] = 0;
        printf("reach k\n");
    }
      if (i)
        break;
  }
}