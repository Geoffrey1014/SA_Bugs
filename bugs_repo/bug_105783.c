void __analyzer_eval(int a) {}

struct ss_s {
    union out_or_counting_u {
    	char *newstr;
    	unsigned long long cnt;
    } uu;
    _Bool counting;
};

struct ss_s ss_init(void) {
   struct ss_s rr = { .counting = 1 };
   return rr;
}

void ss_out(struct ss_s *t, char cc) {
    __analyzer_describe (0, t->counting);
    __analyzer_eval(t->counting == 0);
   if (!t->counting) {
    //    __analyzer_eval(t->counting == 0);
    
       *t->uu.newstr++ = cc;
   }
}

int main() {
    struct ss_s ss = ss_init();
    __analyzer_describe (0, ss.counting);
    // __analyzer_eval(ss.counting == 0);
    ss_out(&ss, 'a');
}
