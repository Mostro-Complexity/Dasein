
```golang
// 包名称
package main

// 导入包名称
import math 
from math import pow
import abcdefg as newname

// 声明结构体
type student struct {
    grade: int32
    age: uint8
    name: string
}

// 实例化未初始化的结构体（字段均为随机值）
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
func init_student(grade: int32, age: uint8, name: string) -> student {
    return student{grade: grade, age: age, name: name}
}

// 静态函数
func student::foo_static() -> student {
    return self
}

// 基本成员函数（默认公有）
func student::foo(stu: this, some_val: int64) -> string {
    return string(some_val)
}

// 基本成员函数（私有）
intern func student::foo(stu: this) -> student {
    return this
}

// 接口定义
type human interface {
    foo1(name: string, age: int32) -> string
}

// 程序入口，main函数仅允许使用intern
intern func main(argc: string, argv: [,]interface{}) {
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