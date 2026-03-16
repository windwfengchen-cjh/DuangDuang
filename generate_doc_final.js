const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require('docx');
const fs = require('fs');

// 贾珍珍的问卷数据
const data = {
  enterprise: "现代农业智汇大厦项目",
  industry: "建筑业",
  city: "广州",
  area: "城镇",
  operationRate: "90%-100%",
  operationRateChange: "基本不变",
  orderChange: "基本不变",
  employeeChange: "基本不变",
  migrantRatio: "5%以内",
  positions: "一线生产岗",
  ageRatio: "新生代占比40%-50%（含）（两者相当或老一代略多）",
  gap: "不存在缺口",
  employmentMode: "劳务外包",
  salaryChange: "基本不变",
  costChange: "基本不变",
  h1Demand: "基本不变",
  fullYearDemand: "基本不变",
  h1Revenue: "增长10%以内（含）",
  fullYearRevenue: "增长10%以内（含）"
};

const doc = new Document({
  styles: {
    default: { 
      document: { 
        run: { font: "宋体", size: 24 } 
      } 
    },
    paragraphStyles: [
      { 
        id: "Heading1", 
        name: "Heading 1", 
        basedOn: "Normal", 
        next: "Normal", 
        quickFormat: true,
        run: { size: 28, bold: true, font: "黑体" },
        paragraph: { spacing: { before: 240, after: 120 } }
      },
      { 
        id: "Heading2", 
        name: "Heading 2", 
        basedOn: "Normal", 
        next: "Normal", 
        quickFormat: true,
        run: { size: 24, bold: true, font: "黑体" },
        paragraph: { spacing: { before: 180, after: 80 } }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      // 标题
      new Paragraph({
        alignment: "center",
        children: [new TextRun({ text: "关于企业农民工用工情况的调研提纲", bold: true, size: 32, font: "黑体" })],
        spacing: { after: 400 }
      }),

      // 一、基本情况
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: "一、基本情况" })]
      }),

      // （一）企业生产经营情况
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（一）企业生产经营情况" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: `${data.enterprise}经营业务是建筑施工，所属行业是${data.industry}，所在地区${data.area}。截至填报日，${data.enterprise}开工率${data.operationRate}，较2025年同期${data.operationRateChange}。今年以来新签订单量${data.orderChange}。`
        })],
        spacing: { after: 200 }
      }),

      // （二）农民工用工情况
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（二）农民工用工情况" })]
      }),
      new Paragraph({
        children: [new TextRun({ text: "数量情况：", bold: true })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: `目前，${data.enterprise}现有员工人数稳定（包括正式员工和外包），较2025年同期${data.employeeChange}。其中农民工人数占总员工比例${data.migrantRatio}，主要集中在${data.positions}。"新生代"与"老一代"农民工的比例构成为${data.ageRatio}。${data.gap}。`
        })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "用工模式：", bold: true })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: `主要采取${data.employmentMode}用工模式。`
        })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ text: "待遇情况：", bold: true })],
        spacing: { after: 100 }
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: `目前农民工工资同比${data.salaryChange}。`
        })],
        spacing: { after: 200 }
      }),

      // （三）预期用工情况
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（三）预期用工情况" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: `预计2026年上半年、全年营业收入同比${data.h1Revenue}、${data.fullYearRevenue}。主要原因是市场环境基本稳定。预计上半年、全年农民工用工需求${data.h1Demand}、${data.fullYearDemand}。`
        })],
        spacing: { after: 300 }
      }),

      // 二、值得关注的问题
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: "二、值得关注的问题（请至少提供一个案例）" })]
      }),

      // （一）
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（一）农民工返乡就业创业意愿有所增强，但乡镇就业容量与渠道仍有待拓展" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "调研发现，受宏观经济形势不确定、大城市生活成本上升以及家庭照护需求等因素影响，越来越多农民工将返乡就业作为重要选项。然而，乡镇企业和欠发达地区产业基础薄弱、产业链条短、规模以上企业数量有限，难以提供足够的、有吸引力的就业岗位。一方面，现有乡镇企业多以资源初加工、来料加工或小型商贸为主，用工需求零散，且普遍存在"小、散、弱"特点，吸纳就业能力不足；另一方面，由于乡镇在物流、网络等基础设施配套上的先天不足，发展农村电商、现代休闲农业、乡村文旅等新业态的条件有限，就业渠道过于单一、现有岗位质量不高，导致部分农民工在返乡与外出之间反复摇摆，难以实现稳定就业。"
        })],
        spacing: { after: 200 }
      }),

      // （二）
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（二）制造业与服务业协同发展放大"技能鸿沟"，工人面临技能适配与提升困境" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "2月发布的《广东省制造业与服务业协同发展白皮书》勾勒"两业融合"新路径。随着制造业智能化改造加速、生产性服务业专业化水平提升，企业对农民工的用工需求正经历结构性调整，智能制造、生产性服务业人才缺口大，但低技能岗位收缩、转型无门。一方面，传统低端岗位大幅缩减，数字化、复合型技能成为新门槛。现代农业智汇大厦项目反映应聘的农民工大多没有接受过正规的职业技能培训，缺乏相关系统化操作技术，在劳动市场上也较少拥有相关职业资格证书或技术的农民工。另一方面，受制于农民工高流动性的特点，企业承担岗前、在岗培训的经济与时间成本高，制约了企业投入资金进行深度的专业技能培养的意愿，导致现有工人技能与企业技术升级、自动化改造需求不匹配，只能继续从事一线重体力或重复性机械劳动。"
        })],
        spacing: { after: 200 }
      }),

      // （三）
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（三）农民工权益保障重视程度不足，企业面临合规风险与短期雇佣困境" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "一方面，农民工为追求极度灵活与短期现金收益，导致不签合同、不愿参保现象普遍。例如有企业表示，工地上大多是包工头招人来干项目，很多是熟人、亲戚，觉得没必要签，有时在这里干几天就得去找别的活干，签合同反而受约束。同时，相当比例的农民工主动要求企业不交社保以换取更更多的现金收入。企业若顺应工人要求不签合同、不缴社保，将面临合规风险；若强制缴纳社保、签合同，则会导致工人流失，两难抉择难以破局。另一方面，权益保障不充分削弱农民工归属感，企业难以建立长期雇佣预期。部分农民工在工伤保险、医疗保险，尤其是养老保险的参保和接续方面仍存在障碍，随迁子女教育等方面的保障不足，无法在工作地获得教育资源，也一定程度上影响农民工就业稳定性。大部分工人选择离职返乡，或选择一个更宜居的城市工作。"
        })],
        spacing: { after: 200 }
      }),

      // （四）
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（四）农民工队伍老龄化趋势加剧，企业面临用工结构与安全保障双重压力" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "随着第一代农民工逐渐步入高龄阶段，我国农民工群体老龄化趋势日益凸显。一方面，由于重体力劳动对身体的长期透支，高龄农民工在工作岗位上发生机械伤害、跌倒乃至突发心脑血管疾病的概率显著增加，企业面临工伤风险上升、商业保险难覆盖等问题。调查显示，现代农业智汇大厦项目负责人表示，目前厂区一线普工的平均年龄适中，由于部分工人超龄无法缴纳常规工伤保险，企业不得不每年额外掏出数万元购买商业意外险。另一方面，受高危行业"清退令"及安全生产规范限制，大批高龄熟练工被迫退出一线，而新生代农民工对枯燥、高强度、无保障的岗位接受度较低，导致企业一线岗位"青黄不接"，面临无人可用的局面。调查显示，现代农业智汇大厦项目负责人表示，即便开出较高的日薪，也难以招聘到愿意干活的年轻人。"
        })],
        spacing: { after: 200 }
      }),

      // （五）- 根据贾珍珍答案修改
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（五）就业质量不高，劳动关系短期化、碎片化特征明显" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "以现代农业智汇大厦项目为例，该企业采用劳务外包用工模式，农民工流动性极强，劳动合同签订比例仅为0%-50%。调研显示，该企业"不存在农民工用工缺口"，但员工稳定性极差——农民工多以短期务工为主，项目周期短、人员流动快，"干一天算一天"的零工特征明显。企业坦言，制约签订合同的主要因素是"农民工流动性强，短期务工为主"，部分工人干几天就要去找别的活干，觉得签合同反而受约束。这种高流动性直接导致劳动关系高度碎片化，农民工难以建立稳定的雇佣预期。"
        })],
        spacing: { after: 200 }
      }),

      // （六）- 根据贾珍珍答案修改
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（六）社会保障覆盖不足，公共服务可及性有待提升" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "现代农业智汇大厦项目农民工社保参保比例仅为0%-50%，且企业未为农民工购买任何保险。调研显示，制约参保的主要因素包括：农民工主动要求不参保（换取更多现金收入），以及农民工流动性强，参保接续不便。企业若顺应工人要求不签合同、不缴社保，将面临合规风险；若强制缴纳，则会导致工人流失，陷入两难困境。此外，子女教育问题成为农民工离职返乡的重要推手——该企业明确表示，"子女无法在务工地入学或参加高考"是农民工选择离开的主要原因，公共服务可及性不足直接导致家庭化迁移受阻。"
        })],
        spacing: { after: 300 }
      }),

      // 三、建议
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: "三、建议" })]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（一）推广灵活用工保障机制，破解劳务外包人员权益保障难题" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "针对建筑业等劳务外包普遍、用工流动性强的行业，建议建立"按项目参保"的工伤保险制度，允许农民工按工程项目而非按劳动关系参加工伤保险，解决"干一天算一天"零工模式下无保障的问题。同时，探索建立农民工工资支付保障金制度和用工实名制平台，将劳动合同签订、考勤记录、工资发放等信息纳入平台监管，既保障农民工合法权益，又为企业规范用工提供抓手。对于短期务工人员，可推行"电子劳动合同+灵活社保"模式，降低参保门槛，实现"干一天保一天"，提高农民工参保意愿。"
        })],
        spacing: { after: 200 }
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（二）深化社保制度改革，打通跨省转移接续堵点" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "针对农民工"流动性强、参保接续不便"的核心痛点，建议进一步优化全国社保转移接续平台功能，实现养老保险、医疗保险跨省转移"一网通办"，缩短办理时限，降低转移成本。对于建筑业等季节性用工行业，探索建立"个人账户+统筹账户"分离机制，允许农民工个人账户随人走、统筹账户分段计，确保"缴了不白缴"。同时，加大对企业社保补贴力度，对吸纳农民工就业并依法参保的企业给予社保费率优惠或专项补贴，降低企业用工成本，提高企业参保积极性，从根本上扭转"企业不愿缴、工人不想缴"的双重困局。"
        })],
        spacing: { after: 200 }
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "（三）推进公共服务均等化，破解农民工子女教育难题" })]
      }),
      new Paragraph({
        children: [new TextRun({ 
          text: "针对"子女无法在务工地入学或参加高考"这一导致农民工返乡的核心痛点，建议深化户籍制度改革，推动教育、医疗等公共服务与户籍逐步脱钩，建立以居住证为主要依据的公共服务供给制度。在义务教育阶段，进一步降低农民工随迁子女入学门槛，扩大公办学校接收容量，保障"应入尽入"；在升学考试阶段，扩大随迁子女在务工地参加中考、高考的范围，逐步打破"高考移民"限制。同时，加大对农民工聚居区教育资源的投入，通过新建、改扩建学校，增加学位供给，让农民工子女"有学上、上好学"，从源头上减少因子女教育问题导致的"被迫返乡"，稳定企业用工队伍。"
        })],
        spacing: { after: 200 }
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/admin/openclaw/workspace/调研提纲_贾珍珍_最终版.docx", buffer);
  console.log("文档已生成：/home/admin/openclaw/workspace/调研提纲_贾珍珍_最终版.docx");
});
