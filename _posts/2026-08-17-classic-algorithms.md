---
title: 经典算法和C++技巧指南
date: 2026-08-17 21:45:00 +0800
categories: [Tutorial]
tags: [algorithm, C++, 算法]
pin: false
math: true
---

在AI盛行的今天，仍有一些比赛、技术面试、考试需要我们熟练地掌握各类算法，并能用一款编程语言在尽可能短的时间内手搓代码解决问题。这项技能从我们学习编程的第一天就开始培养，又在实际工作中逐渐生疏——我们常常遇到曾经已经解决的问题再度变成不会的难题的情况，对STL的熟练度也往往会成为成败的分水岭。笔者最近正好需要在短时间内准备一场比赛，为了不坑队友，决定花一点时间梳理一下常用的知识。

本文不是按照由难到易或者由易到难的顺序组织的，而是按照笔者多年来对**容易遗忘程度**进行排序的，排在前面的是那些如果背不出基本只能放弃的特定算法，接着是一些需要用到STL关键特性的解决方案（如果不会STL，手搓将耗费过多时间），然后是经典的各类算法知识点。希望读者也能从中获益，在临时抱佛脚的时候会感激这篇文章的存在。

## 线段树 - Segment Tree

首先讲一道最基础的需要用线段树解决的题目: [LeetCode 307 Range Sum Query](https://leetcode.com/problems/range-sum-query-mutable)。这道题几乎是线段树的定义和解释——对一个数组保持下面两个特性：(1)支持更新其中的任何一个元素；(2)能快速计算`[left, right)`之间元素的和。

线段树的特性是建树复杂度`O(n)`, 单点修改`O(log n)`，区间求和`O(log n)`。如果不会线段树的实现，区间求和这部分很难临场想出好办法，最笨的办法需要`O(n)`的复杂度计算每次求和，导致超时错误。

假设我们有`nums=[1, 3, 5, 7]`这个数组，线段树的结构大概如下所示。叶子节点都只有一个元素，每个树节点存的是它子节点元素的和。

```text
                      [0,3] = 16
                     /          \
              [0,1] = 4        [2,3] = 12
               /     \           /      \
          [0,0]=1  [1,1]=3  [2,2]=5  [3,3]=7
```

针对每个节点下标`si`，访问子节点的方法是

```C++
left_child = 2 * si + 1;
right_child = 2 * si + 2;
```

这棵树需要多少个节点？计算方法是`2 * pow(2, ceil(log2(n))) - 1`。这个计算公式的原理是这样的：

1. 一颗完全二叉树的叶子节点有L个，那么它总共有2L-1个节点。
2. 把一个长度为n的数组作为完全二叉树的叶子节点，要塞下，这个完全二叉树有多少叶子节点？这个L需要是2的次方，并且至少有n那么大 $2^K >= n$ -> $K >= log_2 n$ -> $K = ceil(log_2 n)$ -> $L = 2 ^ ceil(log_2 n)`$.

下面是这道题的完整解法。

```C++
/**
 * Your NumArray object will be instantiated and called as such:
 * NumArray* obj = new NumArray(nums);
 * obj->update(index,val);
 * int param_2 = obj->sumRange(left,right);
 *//**
 * Your NumArray object will be instantiated and called as such:
 * NumArray* obj = new NumArray(nums);
 * obj->update(index,val);
 * int param_2 = obj->sumRange(left,right);
 */
class NumArray {
public:
    int* segment_tree;
    int size;
    vector<int> nums;
    NumArray(vector<int>& nums) {
        this->size = 2*(int)pow(2, ceil(log2(nums.size())))-1; 
        this->segment_tree = new int[this->size];
        this->nums = nums;
        constructSTUtil(segment_tree, 0, nums.size()-1, 0);
    }
    
    void update(int index, int val) {
        int diff = val - nums[index];
        nums[index] = val;
        updateValueUtil(segment_tree, 0, nums.size()-1, index, diff, 0);
    }
    
    int sumRange(int left, int right) {
        return getSumUtil(segment_tree, 0, nums.size()-1, left, right, 0);
    }
    
    int getSumUtil(int* st, int ss, int se, int qs, int qe, int si) {
        if(qs<=ss && qe>=se){
            return st[si];
        }
        if(se<qs || ss > qe){
            return 0;
        }
        int mid = (ss+se)/2;
        return getSumUtil(st, ss, mid, qs, qe, 2*si+1) + getSumUtil(st, mid+1, se, qs, qe, 2*si+2);
    }
    
    void updateValueUtil(int *st, int ss, int se, int i, int diff, int si) {
        if(i<ss || i>se) {
            return;
        }
        st[si] = st[si] + diff;
        if(se!=ss) {
            int mid = (ss+se)/2;
            updateValueUtil(st, ss, mid, i, diff, 2*si+1);
            updateValueUtil(st, mid+1, se, i, diff, 2*si+2);
        }
    }
    
    int constructSTUtil(int* st, int ss, int se, int si) {
        if(ss==se){
            st[si] = nums[ss];
            return nums[ss];
        }
        int mid = (ss+se)/2;
        st[si] = constructSTUtil(st, ss, mid, si*2+1) + constructSTUtil(st, mid+1, se, si*2+2);
        return st[si];
    }
};
```