void clang_analyzer_eval();

int main()
{
    int a = 0;
    int d = 0;
    int *c = (void *)0;
    int *e = &d;
    clang_analyzer_eval(c == 0);
    for (; a < 4; a++)
    {
        ;
    }
    clang_analyzer_eval(c == 0);
    *e = *c;
}