void __analyzer_eval();

struct a
{
    int b : 6;
} c()
{
    struct a d;
    int e = 2;
    int f = 0;
    if ((d.b = 1) / f)
        if (1 >= d.b <= e)
        {
            __analyzer_eval(0 >= d.b <= e);
        }
}
