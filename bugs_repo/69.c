extern void __analyzer_eval();

int main(void) {
    char buf[] = "0";
    int *ptr = (int *)(__builtin_strlen(buf) - 1);
    __analyzer_eval((__builtin_strlen(buf)) == 1);
    *ptr = 10086;
}