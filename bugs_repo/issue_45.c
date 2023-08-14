

#include <stdbool.h>
#include <stdio.h>

// void clang_analyzer_eval();

struct a b;
struct a {int t;};

int main()
{
    struct a * p = &b;
    if (p == p)
    {
        // clang_analyzer_eval(((&b) + 1) < ((&b) + 2));
        if ((p + 0) < (p + 1))
        {
            printf("hello\n");
        }
    }
}

