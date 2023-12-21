void __analyzer_eval();
void __analyzer_describe();

void c() {
  int d[2] = {42, 43};
  int *e = d;
  if (e == d) {
    __analyzer_describe(0, e);
    __analyzer_describe(0, e + 1);
    __analyzer_describe(0, d + 1);
    __analyzer_eval(e == d + 1);
    __analyzer_eval(e + 1 == d + 1);
  }
}