void clang_analyzer_warnIfReached();

int contains_null_check(int t)
{
    int *p = (void *)t;
    clang_analyzer_eval(t == 0);
    if (p == 0)
    {
        clang_analyzer_eval(p == 0);
        return *p;
    }
    else
    {
        clang_analyzer_eval(p == 0);
        return *p;
    }
}

int main()
{
    if (0)
    {
        clang_analyzer_warnIfReached();
        contains_null_check(1);
    }
}