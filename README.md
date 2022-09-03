
```golang
// 包名称
package main

// 导入包名称
import math 
from math import pow
import abcdefg as newname

// 结构体
student: struct {
    grade: int32: "json:A"  
    age: uint8: "json:B"
    name: string: "json:C"
}

// 条件语句
if a := foo(); a != None {
    a.grade += 1
}

// 函数声明
student::foo: () -> student {
    return self
}
student::foo: noexcept () -> student {
    return self
}
extern student::foo: () -> student {
    return self
}
student::foo := () -> student {
    return self
}

// 接口定义
human: interface {
    foo1: (name: string, age: int32) -> string
}

// 程序入口，main函数仅允许使用extern，否则为内置函数
extern main(argc: string, argv: [,]interface{}) {
    a := [, 4]int32 {   // array, 接近于原生numpy
        {0, 0, 0, 0},
        {1, 2, 3, 4},
        {4, 3, 2, 1},
        {1, 1, 1, 1},
    }
    b := {,}string -> int32 // dict
    aa = a
    print(a) // 编译报错，借用

    for i in range(a) {
        b[string(i), "0"] = aa[i, 0]
        aa[i, :] -= 1
    }

    tuple_arr := []struct{grade: int32, name: string} {
        {grade: 1, name: "bob"}
        {grade: 2, name: "alice"}
    }
}
```