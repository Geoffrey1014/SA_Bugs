#include <stdio.h>
void a(int *e)
{
  printf("NPD_FLAG\n");
  if (e == 0)
  {
    // int *d = 0;
    *e = 1;
  }
}
int main()
{
  int i = 5;
  a(0);
}