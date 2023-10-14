extern void __analyzer_eval();
extern void __analyzer_dump_path();

int a()
{
    int d;
    for (d = -1; d; ++d)
    {
        ;
    }
    __analyzer_dump_path();
    return d;
}

int b()
{
    int t = a();
    int *c = (void *)t;
    __analyzer_eval(c == 0);
    *c = 0;
}

int main() { b(); }