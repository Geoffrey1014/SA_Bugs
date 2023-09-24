void __analyzer_eval();


struct a
{
    int d : 10;
}

e(){
    struct a b;
    int c;

    c = 0;
    b.d = 0;
    int *p = (int *)0;
    if (c || b.d)
    {
        __analyzer_eval(c || b.d);
        __analyzer_eval(c);
        __analyzer_eval(b.d);
        *p = 42;
    }
}

