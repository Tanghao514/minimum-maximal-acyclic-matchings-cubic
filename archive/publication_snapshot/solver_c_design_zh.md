# Solver C 设计说明：三正则图上的边交互森林分支限界算法

## 1. 设计目标

Solver B 按匹配大小递增枚举边集，并利用端点 bitset、诱导森林缓存和容量剪枝求解 minimum maximal acyclic matching。它可靠且适合小规模穷举，但主要瓶颈有三点：

1. 每次扩张都要重新判断完整诱导子图是否为森林；
2. maximality 基本推迟到完整候选处检查；
3. 没有利用三正则图上已经证明的结构下界与分量计数关系。

Solver C 专用于 connected cubic graphs。它不是简单地把 Python 代码换成更快的数据结构，而是把理论证明转化成搜索状态和安全剪枝。

## 2. 匹配边交互图

令候选图边为

\[
e=ab,\qquad f=cd.
\]

对两条候选边预计算三种关系。

### 2.1 端点冲突

若

\[
\{a,b\}\cap\{c,d\}\ne\varnothing,
\]

则二者不能同时属于 matching，记为 endpoint conflict。

### 2.2 强环冲突

假设二者端点不交。记

\[
\lambda(e,f)
=
|E_G(\{a,b\},\{c,d\})|.
\]

若 \(\lambda(e,f)\ge2\)，则四个端点诱导出的图至少有

\[
2+2=4
\]

条边：两条 matching edges 加至少两条跨边。四顶点森林至多有三条边，因此这两个候选不能共同出现在 acyclic matching 中，记为 cycle conflict。

### 2.3 单链接

若二者端点不交且

\[
\lambda(e,f)=1,
\]

则在辅助图中把候选边 \(e,f\) 连起来，称为 link。

## 3. 收缩刻画

给定 matching \(M\)，在 \(G[V(M)]\) 中收缩每一条 matching edge。每一条 matching edge 变成一个辅助顶点，每一条 matching edges 之间的诱导跨边变成辅助边。

由图的边收缩性质可得：

> **收缩刻画。** \(M\) 是 acyclic matching，当且仅当：
> 1. 任意两条被选边之间不存在 endpoint conflict；
> 2. 任意两条被选边之间不存在 cycle conflict；
> 3. 被选边在 link 关系下诱导出的辅助图是一片森林。

因此，Solver C 不再反复构造 \(G[V(M)]\)。它只需在被选 matching edges 上维护一片 link forest。

该森林由 rollback union-find 维护。加入候选边 \(e\) 时，查看它与已选边之间的 link-neighbors：

- 若这些邻点落在同一个现有 DSU 分量中至少两次，则加入 \(e\) 会闭合出环，立即剪枝；
- 否则激活一个新辅助顶点，并把它连接到这些互不相同的分量。

每次回溯只需将 DSU 恢复到快照。

## 4. defect 参数

设当前 acyclic matching 大小为 \(k\)，收缩 link forest 有 \(\delta\) 条边。因为它有 \(k\) 个顶点，所以分量数为

\[
c=k-\delta.
\]

另一方面，理论证明已经得到

\[
n=4k+2(c-t),
\qquad
c\le2t+1.
\]

消去 \(t\) 可得

\[
c\ge n-4k-1,
\]

因此

\[
\boxed{\delta=k-c\le5k+1-n.}
\]

同时 \(c\ge1\)，故

\[
\delta\le k-1.
\]

Solver C 使用的最终预算为

\[
\boxed{
\delta\le
\min\{k-1,\,5k+1-n\}.
}
\]

当搜索第一个理论上可能的目标值

\[
k_0=\left\lceil\frac{n-1}{5}\right\rceil
\]

时，

\[
5k_0+1-n\in\{0,1,2,3,4\}.
\]

所以第一层目标搜索只允许收缩森林出现至多四条 link edges。特别地：

- 若 \(n=5k+1\)，则 defect budget 为 0，被选 matching 必须是 induced matching；
- 其他余数类也只允许 1–4 条额外交互边。

这是 Solver C 相对于 Solver B 最强的结构剪枝。

## 5. 零 defect 的专用支配分支

当

\[
5k+1-n=0,
\]

最终收缩森林必须满足 \(\delta=0\)。此时任意两条入选 matching edges 之间都不能存在 link。因此可把目标重写成一个具有两种关系的独立支配问题：

- **不相容关系**：endpoint conflict、cycle conflict 或 link；
- **支配关系**：选择边自身，或者 endpoint/cycle hard conflict。

为什么 link 不计入支配？因为 \(\delta=0\) 时所有入选边在收缩图中都是孤立点。一条未选边即使只 link 到一个入选边，加入后仍不会闭合环，因此不能依靠单个 link 被 maximality 阻塞。

Solver C 在这一余数类不再做普通组合枚举，而是选择一个尚未被支配的候选边 \(e\)，并分支选择

\[
\{e\}\cup N_{\mathrm{hard}}(e)
\]

中的一个可行候选。任何完整解都必须命中这个集合，所以分支是完备的。选择候选 \(x\) 后：

1. 删除所有与 \(x\) endpoint/cycle/link 不相容的候选；
2. 把 \(x\) 及其 hard-conflict 邻居标记为已支配；
3. 使用 fail-first 规则选择可支配选项最少的未支配边；
4. 使用最大单步覆盖量给出剩余选择数的安全下界；
5. 缓存失败状态 \((A,D,r)\)，其中 \(A\) 为仍可选集合，\(D\) 为已支配集合，\(r\) 为剩余槽位。

这相当于把理论等号情形 \(n=5k+1\) 直接翻译成一个专用 exact subsolver。实测中，\(n=26,k=5\) 的 equality instance 只访问约 10 个递归节点；同一图上 Solver B 需要检查约 \(6.9\times10^4\) 个完整候选。

## 6. maximality 的收缩检查

在完整被选集合 \(M\) 上，考虑未选候选边 \(e\)。

- 若 \(e\) 与某条已选边 endpoint-conflict，则它不能作为 matching edge 加入；
- 若 \(e\) 与某条已选边 cycle-conflict，则加入后立即产生诱导环；
- 否则只需检查 \(e\) 的所有 link-neighbors 在当前 DSU 森林中的根。

若这些根两两不同，加入 \(e\) 只是通过一个新辅助顶点连接若干不同分量，仍为森林，所以当前 matching 不是 maximal。

若至少两个 link-neighbors 已在同一分量中，则加入 \(e\) 会闭合出环，故该边被阻塞。

这一检查与原定义完全等价，但无需对每条未匹配边重新调用 induced-forest oracle。

## 7. near-leaf rigid maximality pruning

当只剩一到两条 matching edges 尚未选择时，Solver C 还使用一条安全的 domination pruning。

对当前仍可扩张的未选边 \(e\)，设未来所有可能被选边的集合为 \(A\)。若 \(e\) 在

\[
M\cup A
\]

中总共至多有一个 link-neighbor，那么无论以后怎样选，加入 \(e\) 都不可能通过“两个 link-neighbors 落入同一分量”而产生环。

因此最终必须发生以下至少一项：

1. 直接选择 \(e\)；
2. 选择一条与 \(e\) endpoint-conflict 的边；
3. 选择一条与 \(e\) cycle-conflict 的边。

这给出一个候选 dominator 集合。对所有这样的 rigid edges 得到一族 hitting-set constraints。因为只在剩余槽位数不超过 2 时使用，Solver C 可以精确检查是否存在大小不超过剩余槽位数的 hitting set；若不存在则立即剪枝。

## 8. 其余剪枝

Solver C 还实现：

- 理论下界直接从 \(\lceil(n-1)/5\rceil\) 开始；
- suffix candidate 数量不足剪枝；
- suffix endpoint union 少于 \(2\cdot\text{need}\) 的容量剪枝；
- defect increments 的最小和超过剩余预算时剪枝；
- 静态高交互边排序与动态 defect-aware 分支排序；
- greedy maximal acyclic matching 作为上界；
- 完整候选处再次检查 \(n=4k+2(c-t)\) 作为内部一致性审计；
- 最终 witness 仍调用定义级 reference routine 复核。

## 9. 正确性边界

Solver C 是精确算法，但其搜索完整性使用了本文的三正则结构定理，尤其是 defect bound。因此：

- 它适合作为定理成立之后的高性能求解器；
- 它不能替代 Solver A、Solver B 或 endpoint-set audit 去独立验证该定理；
- 在论文中应把 A/B/endpoint solver 作为非循环的验证链，把 C 作为“theory-guided exact algorithm”。

## 10. 复杂度

预处理所有候选边对需要

\[
O(m^2)
\]

时间和 \(O(m^2)\) bit relations。

对固定目标 \(k\)，最朴素上界仍是枚举

\[
\binom{m}{k}
\]

个边子集，因此 Solver C 的一般最坏情形仍为指数时间。当前结果不支持声称获得了普遍更小的严格指数底数。

但在三正则图上

\[
m=\frac{3n}{2}.
\]

测试 sharp lower-bound 目标

\[
k_0\approx\frac n5
\]

时，未考虑任何剪枝的组合数量上界约为

\[
\binom{3n/2}{n/5}=O^*(1.803^n),
\]

而 Solver C 还施加 defect \(\le4\)、hard conflicts、link-forest 和 rigid maximality constraints。

### 参数化推论

考虑决策问题：是否存在大小至多 \(K\) 的 maximal acyclic matching？

主定理直接给出：若答案为 YES，则

\[
n\le5K+1.
\]

因此 connected cubic instances 有一个 \((5K+1)\)-vertex kernel：

- 若 \(n>5K+1\)，立即返回 NO；
- 否则保留原实例。

在 kernel 上枚举不超过 \(K\) 条边的候选，给出

\[
O^*\!\left(
\sum_{i=0}^{K}
\binom{(15K+3)/2}{i}
\right)
=
O^*(19.02^K)
\]

的直接 FPT 上界。代码中的

`find_maximal_acyclic_matching_at_most_k_cubic`

实现了 kernel rejection 和精确搜索。

## 11. 当前实测结果

固定环境中，每个受控实例重复 3 次并取中位数。16 个实例全部与 Solver B 返回相同 optimum：

- 全部实例的中位 speedup：约 **5.32×**；
- 7 个 equality-family 实例的中位 speedup：约 **9.99×**；
- 5 个固定随机 cubic 实例的中位 speedup：约 **4.30×**；
- 4 个 16 点反例的中位 speedup：约 **5.49×**；
- \(n=26\) 的零-defect equality case 观测到约 **246.9×** 的中位加速。

小图上预处理开销仍可能抵消部分优势，因此不能宣称对每个实例都严格更快。

消融实验显示，rigid maximality pruning 通常是普通 interaction-forest 搜索中最大的节点削减来源；在旧版 \(n=26\) equality case 中：

- full interaction BnB：985 个递归节点；
- 去掉 rigid pruning：8043 个节点；
- 同时去掉 defect budget 与 rigid pruning：41442 个节点。

加入零-defect 专用分支后，同一 \(n=26\) case 只需约 10 个递归节点。

在显式的 \(n=5k+1\) equality family 上，零-defect subsolver 还测试到 \(n=396\)：返回 \(k=79\)，约 4.6 秒，访问约 40240 个递归节点。该结果只说明专用余数类的扩展能力，不能外推为随机或最坏实例上的多项式时间。

## 12. 验证情况

当前验证包括：

- 项目完整测试：12 passed；
- 对 K4、K3,3、cube、Petersen、10 点 prism 的全部 matching 逐一比较：交互刻画与定义级 acyclicity/maximality 零差异；
- 120 张固定种子的随机 connected cubic graphs 上 Solver B/C optimum 完全一致；
- 所有 4 张 16 点反例返回 \(\mu'_{ac}=3\)；
- equality constructions 在随机插入顺序下与 Solver B 一致。

## 13. 论文中的合适定位

建议把 Solver C 作为一个新的主算法小节：

> **A theory-guided exact solver via the edge-interaction forest.**

核心贡献可以陈述为：

1. matching-edge contraction characterization；
2. rollback-DSU acyclicity maintenance；
3. theorem-derived defect budget；
4. rigid maximality hitting-set pruning；
5. \((5K+1)\)-vertex kernel 与直接 FPT 推论；
6. 与定义级、bitset 和 endpoint-set solvers 的系统交叉验证与消融实验。

不应写成“我们把最坏时间从指数降到多项式”，也不应在未做更广泛 census benchmark 前宣称 universal speedup。
