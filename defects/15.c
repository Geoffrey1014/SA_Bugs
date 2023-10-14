#include "stdio.h"
#include "stdbool.h"
void __analyzer_eval(int);

struct a
{
    int b;
} c()
{
    struct a d = {1};
    int e = 0;
    int *f = (int *)e;

    for (d.b = 0; e == 0; e++)
    {
        __analyzer_eval(false == ((!d.b) && e));
        if ((!d.b) && e)
        {
            __analyzer_eval(false == ((!d.b) && e));
            *f = 42;
        }
    }
}

void main() { c(); }