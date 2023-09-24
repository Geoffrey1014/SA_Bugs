#include "stdio.h"
#include <stdbool.h>
void clang_analyzer_eval();

struct a
{
    int b;
    int c;
};

union d
{
    struct a e
} main()
{
    union d g = {};
    int *p = (int *)0;
    clang_analyzer_eval((-g.e.b && g.e.c) == false);
    if (-g.e.b && g.e.c)
    {
        *p = 42;
    }
}
