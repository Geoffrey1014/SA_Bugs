typedef struct S1 {
    signed f0:32;
} t;

t g_1 = {0};
int main(){
    g_1.f0 = 1;

    t l_1 = {0};
    l_1.f0 = 1;
    int a = 2;
    return 1;
}

// ccomp --version
// The CompCert C verified compiler, version 3.11

// ccomp  -interp -fall -trace -fbitfields  /home/working-space/SA_Bugs/test_data/test-ccomp.c
// Time 0: calling main()
// --[step_internal_function]-->
// Time 1: in function main, statement
//   g_1.f0 = 1; l_1.f0 = 0; l_1.f0 = 1; a = 2; return 1; return 0;
// --[step_seq]-->
// Time 2: in function main, statement
//   g_1.f0 = 1; l_1.f0 = 0; l_1.f0 = 1; a = 2; return 1;
// --[step_seq]-->
// Time 3: in function main, statement g_1.f0 = 1;
// --[step_do_1]-->
// Time 4: in function main, expression g_1.f0 = 1
// --[red_var_global]-->
// Time 5: in function main, expression <loc g_1>.f0 = 1
// --[red_rvalof]-->
// Time 6: in function main, expression <ptr g_1>.f0 = 1
// --[red_field_struct]-->
// Time 7: in function main, expression <loc g_1> = 1
// --[red_assign]-->
// Time 8: in function main, expression 1
// --[step_do_2]-->
// Time 9: in function main, statement /*skip*/;
// --[step_skip_seq]-->
// Time 10: in function main, statement l_1.f0 = 0; l_1.f0 = 1; a = 2; return 1;
// --[step_seq]-->
// Time 11: in function main, statement l_1.f0 = 0;
// --[step_do_1]-->
// Time 12: in function main, expression l_1.f0 = 0
// --[red_var_local]-->
// Time 13: in function main, expression <loc l_1>.f0 = 0
// --[red_rvalof]-->
// Time 14: in function main, expression <ptr l_1>.f0 = 0
// --[red_field_struct]-->
// Time 15: in function main, expression <loc l_1> = 0
// Stuck state: in function main, expression <loc l_1> = 0
// Stuck subexpression: <loc l_1> = 0
// ERROR: Undefined behavior