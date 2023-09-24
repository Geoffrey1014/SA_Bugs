#include "stdio.h"
int main()
{
    int b = 1;
    int e = 2;
    int f = 3;
    int t = 4;
    int *g[] = {&e, &e};
    int *h = &b;
    int *l = &f;
    int *j = &f;

    for (int d = 0; d <= 1; d++)
    {
        *j = *h && (h = g[d]);
    }

    for (int c = 0; c <= 1; c++)
        for (int i = 0; i <= 1; i++)
        {
            int k;
            printf("NPD_FLAG\n");
            k = (l == &l);
        }
}
