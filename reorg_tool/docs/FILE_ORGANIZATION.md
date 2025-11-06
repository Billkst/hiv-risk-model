# HIV风险评估模型 - 文件组织与分类说明

## 📋 文件分类体系

### 🎯 核心文件（必须保留）

这些是项目运行和交付必需的文件。

#### 1. 代码文件（7个）
```
api/
  └── app.py                          # ✅ API服务主程序

models/
  ├── predictor.py                    # ✅ 基础预测器
  ├── enhanced_predictor.py           # ✅ 增强预测器（DG-DAA）
  ├── domain_priors.py                # ✅ 领域知识先验
  ├── feature_contribution_fast.py    # ✅ 特征贡献度分析
  ├── correlation_analyzer.py         # ✅ 相关性分析器
  └── version_manager.py              # ✅ 版本管理器
```

#### 2. 模型文件（2个）
```
saved_models/
  ├── final_model_3to5.pkl           # ✅ 训练好的模型（1.1MB）
  └── model_registry.json            # ✅ 版本注册表
```

#### 3. 配置文件（4个）
```
requirements.txt                      # ✅ Python依赖
Dockerfile                           # ✅ Docker镜像配置
docker-compose.yml                   # ✅ 容器编排
.dockerignore                        # ✅ Docker忽略文件
```

#### 4. 核心文档（6个）
```
README.md                            # ✅ 项目说明（主文档）
USER_MANUAL.md                       # ✅ 用户手册
API_DOCUMENTATION.md                 # ✅ API接口文档
API_USAGE_EXAMPLES.md                # ✅ 使用示例
DEPLOYMENT_GUIDE.md                  # ✅ 部署指南
LOCAL_DEMO_GUIDE.md                  # ✅ 本地演示指南

docs/
  ├── AI_INNOVATION.md               # ✅ 技术创新文档
  └── IMPLEMENTATION_LOG.md          # ✅ 实施日志
```

#### 5. 部署脚本（2个）
```
start.sh                             # ✅ 快速启动脚本
quick_test.sh                        # ✅ 快速测试脚本
```

**核心文件总计**: 21个

---

### 🔧 开发辅助文件（可选保留）

这些文件用于开发、测试和调试，生产环境不需要。

#### 1. 测试脚本（12个）
```
tests/                               # 建议：移到这里
  ├── test_api.py                    # API基础测试
  ├── test_api_simple.py             
---
-34%）
24个文件（**减少**: 00%** |

** | **1 **46** |
| **总计 | 0% |档 | 0% |
| 临时文助 | 25 | 54% |
| 开发辅 | 21 | 46
| 核心文件--|------|-----|----|
|-| 占比 类别 | 数量 案A）

| 
### 整理后（方* |
* | **100%*0** | **7% |
| **总计*24 | 34|  临时文档 36% |
|发辅助 | 25 | % |
| 开| 21 | 30心文件  核---|
|-----|------|- |
|--- 数量 | 占比态

| 类别 |## 当前状
#
## 📊 文件统计---

变

. 核心文件保持不
4`scripts/`本到 移动开发脚chive/`
3.  移动临时文档到 `ar2.ive/` 目录
建 `arch1. 创:


**操作步骤** 占用空间稍大点**:清晰  
**缺: 保留历史，结构*优点**中）

*: 归档方案（折案C

### 方为索引
3. 创建本文档作他文件位置不变. 保持其
2显的临时文档（24个）:
1. 只删除明***操作步骤晰

*: 结构不够清成  
**缺点**最小，快速完: 改动）

**优点**方案B: 最小整理（快速### 

径README中的文件路档
5. 更新/`
4. 删除临时文到 `scripts脚本. 移动开发ocs/`
3移动核心文档到 `d构
2. 目录结
1. 创建新作步骤**:较多文件

**操 需要移动护  
**缺点**:晰，易于维 结构清**:）

**优点组（推荐 完全重
### 方案A:🎯 整理方案
--

## 

-| 1个 | 删除 |档 
| 其他临时文 | | 7个 | 删除文档除 |
| 临时提交 | 2个 | 删临时修复文档 | 删除 |
| 档 | 3个
| 临时测试文或归档 || 删除| 5个 总结文档 删除 |
| 临时2个 | 署文档 | |
| 重复的部 | 删除 文档 | 4个 重复的快速开始----|
|--|------|---
|---------议操作 |量 | 建| 文件类型 | 数可删除或归档**

开发过程中的临时文档，24个）

**文档（ 临时3:### 类别|

loyment/` ep `scripts/d 2个 | 移到部署脚本 |is/` |
| odel_analyspts/mcri3个 | 移到 `s脚本 | 分析g/` |
| 模型cessina_proscripts/dat个 | 移到 `处理脚本 | 4
| 数据 |zation/`visualipts/到 `scri脚本 | 4个 | 移 可视化` |
|g/s/testincript 12个 | 移到 `s试脚本 ||
| 测-----|-----------------|
|--| 建议操作 |数量 文件类型 | *

| /目录*ipts移到scr测试用，可
**开发和
 开发辅助文件（25个） 类别2:持 |

### | 保t.sh` | 测试脚本tesick_qu 保持 |
| ` 启动脚本 |art.sh` || `st
cs/ |到do | 整理核心文档) | .md` (7个docs/*
| `文档 | 保持 |md` | 主
| `README. 保持 |略 |r忽Dockegnore` | ckerido|
| `.持 排 | 保 | 容器编ml`pose.yom
| `docker-c置 | 保持 |r配ockerfile` | DDocke 保持 |
| ` | 依赖 |ts.txt``requiremen
|  模型权重 | 保持 |.pkl` |s/*elsaved_mod|
| `持 码 | 保| 模型代y` (7个) models/*.p保持 |
| `` | API服务 | app.py|
| `api/----|-----------|--|- | 位置 |
件 | 作用
| 文环境需要**
须保留，生产
**必件（21个）
# 类别1: 核心运行文分类详解

## 文件-

## 🗂️
```

-- # 部署检查清单   .md      CKLISTMENT_CHE─ DEPLOY 交付清单
└─       #d     _CHECKLIST.mVERY─ DELI目状态
├─ # 项            md   STATUS.ROJECT_付总结
├── P# 交md      ERY_SUMMARY._DELIVJECT── PRO
├# 快速测试                  ck_test.sh  ├── qui  # 快速启动
                h       rt.sta s略
├──# Docker忽            re        nockerigdo─ .器编排
├─# 容          l     e.ymmposdocker-co├── # Docker配置
               le        ─ Dockerfi赖
├─  # 依            t   uirements.tx档
├── req# 项目主文                  ME.md      
│
├── READ 废弃文件         #      ated/   eprec本
│   └── d     # 临时脚           _scripts/   ├── temp旧文档
│          # s/           old_doc）
│   ├──归档文件（新建   #                    hive/   ─ arc/
│
├─luation─ model_eva/
│   └─on_analysiscorrelati ├── /
│  izationsual─ vis
│   ├─出结果       # 输             uts/      outp
├──sh
│loyment.epack_for_d └── p     │ ment.sh
epare_deploy├── pr      部署脚本
│    #              t/  ── deploymen ...
│   └│   └──ig.py
│   ntion_confize_atte─ optim │   ├─del.py
│  nhanced_moluate_e── eva析
│   │   ├     # 模型分         is/_analys├── model.
│     └── ..s.py
│   │ eck_column── ch   │   ├
│_data.pyrify│   ├── ve 数据处理
│             #essing/   _proc│   ├── data  └── ...
│   │ ns.py
contributiosualize_ vi│   │   ├──eights.py
attention_wze_li   ├── visua脚本
│   │可视化        #      ization/  ualvis.
│   ├──    └── ...py
│   │ionsntributst_co├── te   │   y
│ion.pntatte├── test_py
│   │   pi.test_a ├──    │  脚本
│   # 测试               ng/   sti ├── te  发脚本
│    # 开                    ipts/ cr
│
├── s指南（移到这里）# 演示      d    _GUIDE.m LOCAL_DEMO
│   └──# 部署指南（移到这里）         UIDE.md PLOYMENT_G├── DE
│   里） # 使用示例（移到这  PLES.md     GE_EXAM─ API_USA ├─  I文档（移到这里）
│      # APN.md   TATIODOCUMENPI_─ A  ├─│ 到这里）
册（移用户手          # L.md     NUA USER_MA  ├──
│  实施日志d        #.mOGION_LNTAT├── IMPLEME
│   文档 技术创新       #ION.md      ─ AI_INNOVAT   ├─心文档
│ 核    #                   ocs/      d──raw/
│
├│   └── csv
processed.── hiv_data_ │   └essed/
│     ├── proc 数据文件
│   #              /           ta── day.json
│
├gistr_re modelpkl
│   └──el_3to5.── final_mod件
│   ├   # 模型文               ls/  ved_modesa
│
├── manager.py└── version_zer.py
│   ion_analyorrelat
│   ├── c_fast.pyutionntribture_co├── fea.py
│   omain_priors── d ├.py
│  d_predictorenhance  ├── or.py
│ ├── predict模型代码
│   核心        #          s/         ├── model app.py
│
   └──
│    # API服务                     api/     el/
├──modisk_v_r

```
hi的目录结构

### 📁 建议---

L中）
```R_MANUA（信息已在USE删除 # .md     ONTRIBUTIONVS_C❌ ATTENTION_1个）
```
 8. 其他临时文档（`

#### # 删除
``       t      tx司的预热邮件.❌ 给公   # 删除
                 汇报PPT大纲.md # 删除
❌                   单.md明天提交清   # 删除
❌   文件清单.txt   
❌ 今晚发给公司的    # 删除事.md        要做的ME_今晚
❌ READ       # 删除NTS.md     NCEMEREADME_ENHA❌    # 删除
            T.md  _TO_SUBMI WHAT
❌        # 删除E.md       ON_GUIDSI❌ SUBMIS）
```
档（7个. 临时提交文# 7

###已完复）
```      # 删除（d         AND_TEST.m RESTART_修复）
❌     # 删除（已            RY.md   MMA``
❌ FIX_SU个）
`临时修复文档（26. `

#### 除（已完成）
``      # 删d         MMARY.mX_SU_FI
❌ FONT（已完成）      # 删除LVED.md     ISSUES_RESO❌ TEST_成）
 # 删除（已完            d GUIDE.mTEST_HASE2_
```
❌ P档（3个）测试文. 临时

#### 5_LOG中）
```TATIONPLEMEN 删除（信息已在IM       #            G.md  PDATE_LO时记录）
❌ U# 删除（临                REATED.md  ILES_C项目状态）
❌ F# 保留（                 _STATUS.md PROJECT报告）
✅交付# 保留（正式     MARY.md  ELIVERY_SUMOJECT_Dd）
✅ PRY.m_SUMMARVERY_DELIECTPROJ# 删除（保留           .md     SUMMARYOJECT_）
```
❌ PR结文档（5个# 4. 临时总`

###EADME中）
``删除（信息已在R        #    d FILES.mDELIVERY_E_COR
❌  # 保留（详细检查）         IST.md CHECKLEPLOYMENT_（快速参考）
✅ D    # 保留       LIST.md  CKCHE✅ DELIVERY_```
付清单（2个）
 重复的交## 3.`

##
``   # 删除         明.md   部署准备情况说UIDE.md）
❌ OYMENT_GEPL保留D     # 删除（             .md   YMENTDEPLO
❌ 文档（2个）
```2. 重复的部署``

####      # 删除
`        启动指南.md  测试  # 删除
❌ 本地              RT.md     ❌ QUICKSTA     # 删除
.md      T_ENHANCEDUICK_STARIDE.md）
❌ QMO_GU_DE除（保留LOCAL     # 删             T.md  _STAR❌ QUICK
```
）4个复的快速开始文档（ 重# 1.归档。

###，可以删除或的临时文档这些是开发过程中文档（可删除）

📚 临时

### 

---h
```and_retest.s└── fix_acing.py
  all_sp_waterf里
  ├── fix到这     # 建议：移                 xes/ /fi
scripts）
```. 修复脚本（2个`

#### 5fig.py
``ention_con_attze── optimiize.py
  └el_ste_mod ├── calculaarams.py
 heck_model_p到这里
  ├── c：移    # 建议       /   analysisipts/model_）
```
scr. 模型分析脚本（3个

#### 4py
```report.elation_e_correraty
  └── gen_columns.p ├── check
 erge.pyrify_m─ vea.py
  ├── verify_dat
  ├─议：移到这里       # 建ssing/      _procescripts/data本（4个）
```
 3. 数据处理脚`

####tions.py
``relaoralize_c  └── visus.py
utionlize_contrib─ visua
  ├─on_simple.pye_attentisualiz
  ├── vits.pyghention_weisualize_att里
  ├── vi   # 建议：移到这          ion/  sualizatipts/vi）
```
scr脚本（4个## 2. 可视化估
```

##     # 交叉验证评cv.py       uate_with_  └── eval型评估
l.py     # 模_modehanced_en├── evaluate预测示例
   详细     #ed.pyction_detailpredi
  ├── run_   # 使用示例         .py   xample_usage体测试
  ├── e  # 中文字.py         ese_fontint_ch── tes ├e 2完整测试
 as      # Phpy  e2_complete.hasest_p── t征贡献度测试
  ├   # 特     ns.py  ributio_cont─ test ├─力权重测试
         # 注意    tention.py  test_at  ├── 测试
修复       # API.py         pi_fix_a test功能测试
  ├── API增强 #          enhanced.pytest_api_├── I简单测试
  # AP