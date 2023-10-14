# include <stdint.h>
# include <stdio.h>

int32_t c;
int32_t *b;
int32_t **d = &b;

void e() { b = 0; }
void f() {
  int32_t g = 7;
  e();
  *d = &g;
  printf("NPD_FLAG\n");
  c = *b; //fp of NPD
printf("%d\n", c);
}
int main() { f(); }