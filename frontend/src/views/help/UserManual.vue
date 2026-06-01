<template>
  <Layout>
    <div class="manual-page">
      <div class="manual-split" :class="{ 'manual-split--collapsed': tocCollapsed }">
        <aside class="manual-toc" aria-label="目录">
          <div class="manual-toc-inner">
            <div class="manual-toc-toolbar">
              <span v-show="!tocCollapsed" class="manual-toc-title">目录</span>
              <el-button
                class="manual-toc-toggle"
                circle
                size="small"
                :title="tocCollapsed ? '展开目录栏' : '收起目录栏'"
                @click="tocCollapsed = !tocCollapsed"
              >
                <el-icon>
                  <DArrowRight v-if="tocCollapsed" />
                  <DArrowLeft v-else />
                </el-icon>
              </el-button>
            </div>

            <div v-show="!tocCollapsed" class="manual-toc-scroll">
              <nav class="toc-tree" aria-label="文档结构">
                <div v-for="node in tocTree" :key="node.id" class="toc-tree-root">
                  <div class="toc-row">
                    <button
                      v-if="node.children?.length"
                      type="button"
                      class="toc-caret-btn"
                      :aria-expanded="isExpanded(node.id)"
                      :title="isExpanded(node.id) ? '折叠' : '展开'"
                      @click.stop="toggleExpand(node.id)"
                    >
                      <el-icon class="toc-caret" :class="{ 'toc-caret--open': isExpanded(node.id) }">
                        <CaretRight />
                      </el-icon>
                    </button>
                    <span v-else class="toc-leaf-slot" aria-hidden="true" />

                    <a
                      href="javascript:void(0)"
                      class="toc-link"
                      :class="{ 'toc-link--active': isNodeActive(node.id) }"
                      role="button"
                      @click.prevent="selectSection(node.id)"
                    >
                      {{ node.label }}
                    </a>
                  </div>

                  <div
                    v-if="node.children?.length && isExpanded(node.id)"
                    class="toc-tree-children"
                  >
                    <div v-for="ch in node.children" :key="ch.id" class="toc-row toc-row--child">
                      <span class="toc-leaf-slot" aria-hidden="true" />
                      <a
                        href="javascript:void(0)"
                        class="toc-link toc-link--child"
                        :class="{ 'toc-link--active': activeSectionId === ch.id }"
                        role="button"
                        @click.prevent="selectSection(ch.id)"
                      >
                        {{ ch.label }}
                      </a>
                    </div>
                  </div>
                </div>
              </nav>
            </div>

            <button
              v-if="tocCollapsed"
              type="button"
              class="manual-toc-collapsed-hit"
              title="点击展开目录"
              @click="tocCollapsed = false"
            >
              <span class="manual-toc-collapsed-text">目录</span>
            </button>
          </div>
        </aside>

        <div class="manual-doc">
          <div ref="docBodyRef" class="manual-doc-body">
            <div :key="activeSectionId" class="manual-doc-pane">
              <!-- 项目介绍 -->
              <template v-if="activeSectionId === 'manual-intro'">
                <header class="manual-block manual-intro-block">
                  <h1>使用手册</h1>
                  <p class="manual-lead">
                    欢迎使用<strong>智能笔记助手</strong>。您可以用它整理笔记、写作与复习，并在写作过程中使用 AI
                    生成、总结与翻译等能力。本页面向<strong>日常使用者</strong>说明产品是什么、怎么用以及相关约定。
                  </p>
                  <el-alert type="info" show-icon :closable="false" class="manual-tip">
                    <template #title>
                      <span>温馨提示</span>
                    </template>
                    AI 生成内容由模型概率输出，可能存在错误或过时信息，请结合自身判断使用；不可替代医疗、法律等专业意见。具体菜单与按钮名称以您使用的网页界面为准。
                  </el-alert>

                  <h3 class="manual-h3">本产品能做什么</h3>
                  <ul class="manual-list">
                    <li><strong>笔记</strong>：新建与编辑（富文本或 Markdown）、搜索与管理「我的笔记」、查看历史笔记、从 Word / 文本等导入内容。</li>
                    <li><strong>首页工作台</strong>：左侧管理笔记与导入，中间预览正文，右侧与 AI 对话并可关联某篇笔记作为上下文。</li>
                    <li><strong>AI</strong>：按主题生成笔记草稿、对选定内容做总结分析、多语言翻译；可在个人中心配置<strong>自带模型接口</strong>（可选）。</li>
                    <li><strong>思维导图</strong>：在独立页面查看或整理导图相关内容（见顶部导航）。</li>
                  </ul>

                  <h3 class="manual-h3">从哪里进入各功能</h3>
                  <ul class="manual-list manual-list--compact">
                    <li><strong>首页</strong>：<code>/home</code></li>
                    <li><strong>我的笔记</strong>：<code>/notes</code>；<strong>新建 / 编辑</strong>：<code>/notes/edit</code></li>
                    <li><strong>历史笔记</strong>：<code>/notes/history</code></li>
                    <li><strong>AI 笔记生成</strong>：<code>/ai/generate</code></li>
                    <li><strong>AI 笔记总结</strong>：<code>/ai/summarize</code></li>
                    <li><strong>翻译笔记</strong>：<code>/ai/translate</code></li>
                    <li><strong>思维导图</strong>：<code>/mindmap</code></li>
                    <li><strong>个人中心</strong>：<code>/user</code></li>
                  </ul>
                  <p class="manual-p manual-muted">
                    登录后可使用上述页面；未登录时请先注册或登录。
                  </p>
                </header>
              </template>

              <!-- 用户协议 -->
              <section v-else-if="activeSectionId === 'manual-terms'" class="manual-block">
                <h2>用户协议</h2>
                <p class="manual-p">
                  在使用本网站及相关功能前，请您仔细阅读下列条款。您注册、登录或使用服务即表示您已阅读并接受本协议约定。
                </p>

                <h3 class="manual-h3">服务内容</h3>
                <p class="manual-p">
                  本服务向您提供笔记存储与管理、以及可选的 AI 辅助功能（如生成、总结、翻译与对话）。具体功能以线上界面实际提供的为准，我们可能在不另行通知的情况下优化或调整功能布局。
                </p>

                <h3 class="manual-h3">账号与安全</h3>
                <ul class="manual-list">
                  <li>您应使用真实、合法的信息注册，并妥善保管用户名与密码；因密码泄露导致的损失由您自行承担。</li>
                  <li>请勿将账号出借、转让给他人用于违法违规用途。</li>
                  <li>如发现账号异常，请及时修改密码并停止使用可疑设备登录。</li>
                </ul>

                <h3 class="manual-h3">使用规范</h3>
                <ul class="manual-list">
                  <li>您在使用 AI 功能时输入或生成的内容，不得违反法律法规，不得侵害他人知识产权、名誉权、隐私权等合法权益。</li>
                  <li>请勿利用本服务传播骚扰信息、恶意代码，或对系统进行攻击、爬取与过载请求。</li>
                  <li>对您上传、发布的笔记内容及 AI 输出，您应保证有权使用该等内容；由此引发的争议由您自行负责。</li>
                </ul>

                <h3 class="manual-h3">知识产权</h3>
                <p class="manual-p">
                  本应用的界面设计、程序与文案等由开发者享有相应权利。您在服务中创作的笔记内容之权利归属，在不违反法律的前提下由您享有；您授予我们为提供存储与展示服务所必需的、非独占的使用许可。
                </p>

                <h3 class="manual-h3">免责声明</h3>
                <ul class="manual-list">
                  <li>AI 输出具有不确定性，我们不保证其准确性、完整性或适用于任何特定目的。</li>
                  <li>因不可抗力、网络故障、第三方服务不可用等原因导致的服务中断或数据异常，我们将在合理范围内尽力修复，但不承担由此造成的间接损失。</li>
                  <li>您在做出重要决策前，应自行核实关键信息。</li>
                </ul>

                <h3 class="manual-h3">协议变更与终止</h3>
                <p class="manual-p">
                  我们可能适时修订本协议，修订后的内容在本页面更新后生效。若您继续使用服务，即视为接受修订。您可随时停止使用并注销账号（若产品提供相应入口）；我们亦有权在法律法规允许的前提下暂停或终止向违规用户提供服务。
                </p>
              </section>

              <!-- 隐私说明 -->
              <section v-else-if="activeSectionId === 'manual-privacy'" class="manual-block">
                <h2>隐私说明</h2>
                <p class="manual-p">
                  我们重视您的个人信息与内容安全。本说明描述我们如何处理与您使用本服务相关的数据；具体技术实现可能随版本迭代优化，请以本页最新表述为准。
                </p>

                <h3 class="manual-h3">我们收集哪些信息</h3>
                <ul class="manual-list">
                  <li><strong>账号信息</strong>：注册与登录所需的用户名、电子邮箱等（以注册页字段为准）。</li>
                  <li><strong>笔记与内容</strong>：您主动创建、编辑或导入的笔记正文、标题与标签等。</li>
                  <li><strong>使用过程数据</strong>：为保障服务与安全，服务端可能记录必要的日志（例如操作时间、功能调用次数统计等），用于排查故障与改进体验。</li>
                  <li><strong>可选：自带模型配置</strong>：若您在个人中心填写推理服务的 API 基址、模型名称与密钥，我们将在您确认保存后接收并<strong>加密存储</strong>密钥类信息，用于按您的指示调用第三方兼容接口。</li>
                </ul>

                <h3 class="manual-h3">我们如何使用</h3>
                <ul class="manual-list">
                  <li>用于向您提供登录、笔记同步、AI 能力与界面展示。</li>
                  <li>用于保障系统安全、防止欺诈与滥用。</li>
                  <li>除法律法规要求或经您明确同意外，我们不会将您的笔记内容用于与本服务无关的商业画像或对外出售。</li>
                </ul>

                <h3 class="manual-h3">Cookies 与登录状态</h3>
                <p class="manual-p">
                  为保持登录状态，浏览器可能保存令牌或会话信息（具体机制由产品实现决定）。请勿在公共设备上勾选「记住我」类选项后离开而未退出登录。
                </p>

                <h3 class="manual-h3">第三方与 AI</h3>
                <p class="manual-p">
                  当您使用 AI 功能时，相关内容需发送至本站连接的推理服务（或由您配置的自带接口）进行处理。请选择您信任的接口提供方，并避免在对话或上传文件中包含高度敏感的个人信息。
                </p>

                <h3 class="manual-h3">您的权利与联系我们</h3>
                <p class="manual-p">
                  您可通过个人中心管理头像与密码等信息；若需更正账号资料或注销诉求，请通过本手册末尾<strong>反馈与缺陷报告</strong>中的联系方式与我们沟通，我们将在核实身份后依法予以配合。
                </p>
              </section>

              <!-- 账号与个人资料 -->
              <section v-else-if="activeSectionId === 'manual-account'" class="manual-block">
                <h2>账号与个人资料</h2>

                <h3 class="manual-h3">注册</h3>
                <ol class="manual-list">
                  <li>在欢迎页点击<strong>免费注册</strong>（或进入 <code>/register</code>）。</li>
                  <li>按页面提示填写必填项并完成注册。</li>
                  <li>注册成功后使用用户名与密码登录。</li>
                </ol>

                <h3 class="manual-h3">登录与退出</h3>
                <ol class="manual-list">
                  <li>在欢迎页点击<strong>立即登录</strong>（或进入 <code>/login</code>），输入用户名与密码。</li>
                  <li>登录成功后一般会进入<strong>首页</strong>；若先前访问过需登录的页面，登录后可能会回到该页面。</li>
                  <li>退出：点击右上角<strong>用户名</strong>，在下拉菜单中选择<strong>退出登录</strong>。</li>
                </ol>

                <h3 class="manual-h3">个人中心 · 个人信息</h3>
                <p class="manual-p">
                  打开顶部导航<strong>个人中心</strong>（<code>/user</code>）。在<strong>个人信息</strong>卡片中点击<strong>展开</strong>，可查看用户名、邮箱、注册时间；点击头像区域可按提示<strong>更换头像</strong>（支持的格式与大小以页面提示为准）。
                </p>

                <h3 class="manual-h3">个人中心 · 数据统计</h3>
                <p class="manual-p">
                  <strong>数据统计</strong>卡片展开后，可查看笔记数量、AI 使用次数、活跃天数等汇总指标；部分卡片支持点击跳转到对应页面（以界面为准）。
                </p>

                <h3 class="manual-h3">修改密码</h3>
                <p class="manual-p">
                  在个人中心找到<strong>安全设置</strong>卡片，展开后填写<strong>当前密码</strong>、<strong>新密码</strong>（至少 6 位）与<strong>确认密码</strong>，保存即可。
                </p>
              </section>

              <!-- AI 与自带模型 -->
              <section v-else-if="activeSectionId === 'manual-ai-byok'" class="manual-block">
                <h2>AI 与自带模型</h2>
                <p class="manual-p">
                  当您希望使用自己申请的兼容接口（而非站点默认线路）时，可在<strong>个人中心 → AI 模型（自带密钥）</strong>中配置。展开该区域后按表单填写并保存。
                </p>

                <h3 class="manual-h3">何时需要配置</h3>
                <ul class="manual-list">
                  <li>页面提示 AI 不可用或您希望固定使用某一自建 / 第三方兼容服务时，可在征得服务条款允许的前提下填写自带接口。</li>
                  <li>若不填写或留空部分字段，通常表示继续使用站点为您准备的默认推理配置（以实际表现为准）。</li>
                </ul>

                <h3 class="manual-h3">填写说明</h3>
                <ul class="manual-list">
                  <li><strong>API 基址</strong>：须为您所用服务的 <strong>OpenAI 兼容根路径</strong>，一般以 <code>/v1</code> 结尾，例如 <code>https://示例域名/api/v1</code>。<strong>不要</strong>把浏览器里常见的 <code>…/v1/models</code> 整条地址当作基址填入。</li>
                  <li><strong>模型标识</strong>：须与推理软件或服务列表里显示的<strong>模型名称</strong>完全一致。</li>
                  <li><strong>API 密钥</strong>：仅在您信任本站点存储的前提下填写。密钥在服务端以加密方式保存；若站点安全策略发生重大变更，您可能需要重新保存一次密钥。</li>
                  <li>修改已保存的密钥：按界面提示开启<strong>修改 API Key</strong>后再保存；留空并保存可能表示清除已保存的个人密钥。</li>
                </ul>

                <el-alert type="warning" show-icon :closable="false" class="manual-tip">
                  请勿在公共场合泄露密钥；不要使用他人账号或来路不明的接口。
                </el-alert>
              </section>

              <!-- 功能说明 · 父级 -->
              <section v-else-if="activeSectionId === 'manual-features'" class="manual-block">
                <h2>功能说明</h2>
                <p class="manual-p">
                  请在左侧目录中<strong>展开</strong>本条目，并点击某一具体功能，右侧将只展示该功能的详细步骤。
                </p>
              </section>

              <!-- 功能说明 · 子项 -->
              <section v-else-if="activeFeatureItem" class="manual-block">
                <p class="manual-crumb">功能说明</p>
                <h2>{{ activeFeatureItem.title }}</h2>
                <p v-if="activeFeatureItem.routeHint" class="manual-route-hint">
                  页面路径：<code>{{ activeFeatureItem.routeHint }}</code>
                </p>
                <p v-for="(para, idx) in activeFeatureItem.paragraphs" :key="'p-' + idx" class="manual-p">
                  {{ para }}
                </p>
                <template v-for="sec in activeFeatureItem.sections" :key="sec.title">
                  <h3 class="manual-h3">{{ sec.title }}</h3>
                  <ul class="manual-list">
                    <li v-for="(item, i) in sec.items" :key="i">{{ item }}</li>
                  </ul>
                </template>
              </section>

              <!-- 常见问题 -->
              <section v-else-if="activeSectionId === 'manual-faq'" class="manual-block">
                <h2>常见问题</h2>
                <ul class="manual-list">
                  <li>
                    <strong>AI 一直没反应或报错</strong>：请先检查网络；稍后重试。若您已配置自带模型，请核对 API 基址是否以
                    <code>/v1</code> 结尾、模型名称是否正确。仍无法使用时，请通过<strong>反馈与缺陷报告</strong>联系我们。
                  </li>
                  <li>
                    <strong>首页导入笔记失败或提示文件过大</strong>：首页<strong>导入笔记</strong>通常支持
                    <code>.docx</code>、<code>.txt</code>、<code>.md</code>；单文件大小请勿超过页面提示上限（例如 20MB）。
                  </li>
                  <li>
                    <strong>翻译提示超出字数</strong>：服务端在将正文（含 HTML）转为 Markdown 后，会按最多约 8000 字符截断再翻译；过长时请分段或精简。译文可能带有「笔记助手」等水印标识。
                  </li>
                  <li>
                    <strong>切换页面后表单还在吗</strong>：多数 AI 与笔记相关页面使用了路由缓存，来回切换时常会保留已填写内容；若您<strong>刷新浏览器</strong>或<strong>关闭标签页</strong>，未保存内容可能丢失。
                  </li>
                  <li>
                    <strong>预览与编辑显示不一致</strong>：Markdown / HTML 渲染规则以编辑器与预览区域为准；涉及复杂排版时建议在保存前核对最终效果。
                  </li>
                </ul>
                <p class="manual-p">
                  更多使用疑问或缺陷报告，请查看<strong>反馈与缺陷报告</strong>一节。
                </p>
              </section>

              <!-- 反馈与缺陷报告 -->
              <section v-else-if="activeSectionId === 'manual-feedback'" class="manual-block">
                <h2>反馈与缺陷报告</h2>
                <p class="manual-p">
                  感谢您使用本产品。若在体验中遇到界面异常、功能错误或文档未覆盖的问题，欢迎向开发者发送邮件，便于我们修复与改进。
                </p>

                <el-alert type="info" show-icon :closable="false" class="manual-tip">
                  <template #title>
                    <span>开发者邮箱</span>
                  </template>
                  <p class="manual-mail-block">
                    <a class="manual-mailto" :href="FEEDBACK_MAILTO">{{ FEEDBACK_EMAIL }}</a>
                  </p>
                  <p class="manual-p manual-p--tight">
                    点击邮箱将尝试打开您设备上的邮件客户端（支持 <code>mailto:</code> 的环境）。
                  </p>
                </el-alert>

                <h3 class="manual-h3">建议在邮件中写明</h3>
                <ul class="manual-list">
                  <li><strong>问题简述</strong>：一句话概括现象。</li>
                  <li><strong>复现步骤</strong>：按顺序写「第一步…第二步…」，便于我们重现。</li>
                  <li><strong>出现位置</strong>：哪个菜单或页面路径（例如首页、翻译笔记）。</li>
                  <li><strong>环境与时间</strong>：浏览器类型与版本、大致发生时间。</li>
                  <li><strong>截图或录屏</strong>（可选）：若有报错提示或界面错位，附件非常有帮助。</li>
                </ul>
              </section>

              <!-- 关于本文档 -->
              <footer v-else-if="activeSectionId === 'manual-more'" class="manual-block manual-footer">
                <h2 class="manual-footer-title">关于本文档</h2>
                <p class="manual-p">
                  本使用手册随产品迭代更新，章节标题与操作路径以您当前打开的网页为准。若界面已调整而本文尚未同步，请以线上实际按钮与提示为准。
                </p>
                <p class="manual-p">
                  缺陷与建议欢迎发送至
                  <a class="manual-inline-link" :href="FEEDBACK_MAILTO">{{ FEEDBACK_EMAIL }}</a>
                  （详见<strong>反馈与缺陷报告</strong>）。
                </p>
                <p class="manual-muted">文档版本：与当前应用前端版本同步维护。</p>
              </footer>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'
import { CaretRight, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import Layout from '@/components/Layout.vue'

defineOptions({
  name: 'UserManual'
})

const FEEDBACK_EMAIL = 'pm1993748944@outlook.com'
const FEEDBACK_MAILTO = `mailto:${FEEDBACK_EMAIL}?subject=${encodeURIComponent('笔记助手 · 反馈 / 缺陷报告')}`

const FEATURE_ITEMS = [
  {
    id: 'manual-feature-home',
    title: '首页',
    routeHint: '/home',
    paragraphs: [
      '首页是您登录后的工作台，采用左中右三栏布局：左侧管理笔记入口与最近列表，中间预览正文，右侧与 AI 对话。'
    ],
    sections: [
      {
        title: '左侧 · 笔记管理',
        items: [
          '点击「新建笔记」进入编辑器创建空白笔记。',
          '点击「导入笔记」可选择本地文件（支持类型与大小限制以弹窗或提示为准）。',
          '「最近笔记」列出近期条目，点击后在中间栏预览。',
          '列表较长时可能出现「更多」入口，用于前往历史笔记浏览更早的内容。'
        ]
      },
      {
        title: '中间 · 预览',
        items: [
          '在中间栏阅读当前选中笔记的正文（渲染方式与编辑器一致）。',
          '若该笔记尚未加入收藏列表，可使用「加入我的笔记」，之后在「我的笔记」列表中统一管理。',
          '使用「编辑」进入笔记编辑页进行修改。'
        ]
      },
      {
        title: '右侧 · AI 助手',
        items: [
          '在输入框输入问题并发送，可与 AI 多轮对话。',
          '标题栏提示：本地最多保留一定数量的聊天记录，超出后较早的消息会自动丢弃（具体条数以页面说明为准）。',
          '可使用「清空对话」重置当前会话记录。',
          '在输入框输入「/note」（按页面提示操作）可从您的笔记中选择一篇作为上下文，便于 AI 结合笔记回答。',
          '界面上的快捷按钮（若有）可一键发起一类常见问题；附件上传（若有）按区域说明操作。'
        ]
      }
    ]
  },
  {
    id: 'manual-feature-notes',
    title: '我的笔记',
    routeHint: '/notes、/notes/edit、/notes/history',
    paragraphs: [
      '「我的笔记」集中展示您已收藏纳入管理的笔记；新建与编辑在独立页面完成；历史笔记用于按时间线查看更早的条目。'
    ],
    sections: [
      {
        title: '我的笔记列表（/notes）',
        items: [
          '顶部搜索框可按标题或正文关键词查找。',
          '「创建笔记」进入新建页。',
          '列表中为已「加入我的笔记」的条目，卡片上可进行查看、编辑、删除等操作（以实际按钮为准）。'
        ]
      },
      {
        title: '新建与编辑（/notes/edit）',
        items: [
          '填写标题；标签多个时建议用英文逗号分隔。',
          '正文支持「富文本」与「Markdown」两种模式，可通过页面上方切换。',
          'Markdown 模式下一般为左侧编辑、右侧预览（亦支持部分 HTML，具体以渲染为准）。',
          '完成后点击「保存」。'
        ]
      },
      {
        title: '历史笔记（/notes/history）',
        items: [
          '用于浏览历史上创建或导入的笔记时间线（展示样式以页面为准）。',
          '导入成功后条目可能默认出现在历史中；若需在日常列表中固定查看，可在预览时将其「加入我的笔记」。'
        ]
      }
    ]
  },
  {
    id: 'manual-feature-import',
    title: '导入笔记',
    routeHint: '首页 /home · 「导入笔记」',
    paragraphs: [
      '在首页左侧点击「导入笔记」，从本地选择文件。常见支持格式包括 Word（.docx）、纯文本（.txt）与 Markdown（.md）；若上传被拒，请查看页面报错中的格式或大小说明。'
    ],
    sections: [
      {
        title: '操作建议',
        items: [
          '单文件体积请勿超过页面提示上限（例如 20MB）。',
          '导入成功后笔记通常可在「历史笔记」中找到；默认未必出现在「我的笔记」，需要时请手动「加入我的笔记」。',
          '若因同名等原因出现覆盖或合并提示，请仔细阅读对话框后再确认。'
        ]
      }
    ]
  },
  {
    id: 'manual-feature-gen',
    title: 'AI 笔记生成',
    routeHint: '/ai/generate',
    paragraphs: [
      '根据您填写的主题与关键词，由 AI 自动生成一篇笔记草稿；可选择输出为 Markdown、Word 或纯文本，并可将结果保存到笔记或下载。'
    ],
    sections: [
      {
        title: '填写与生成',
        items: [
          '「笔记主题」为必填，概括要写的内容。',
          '「补充关键词」可选，多条建议用逗号分隔。',
          '「期望字数」通过滑块选择大致篇幅（界面会标注简洁 / 标准 / 详细等区间）。',
          '「输出格式」在 Markdown、Word 文档、纯文本中选择其一。',
          '若有「参考笔记」「参考图片」上传区，请按区域说明添加；已选文件列表以上传组件展示为准。',
          '点击「开始生成」后请耐心等待；完成后在结果区查看，并可使用保存、复制、下载等按钮（以页面为准）。'
        ]
      }
    ]
  },
  {
    id: 'manual-feature-sum',
    title: 'AI 笔记总结',
    routeHint: '/ai/summarize',
    paragraphs: [
      '对选定笔记或粘贴文本进行分析，生成摘要、建议与质量评估类展示（含图表等，以页面为准）。'
    ],
    sections: [
      {
        title: '操作步骤',
        items: [
          '在左侧「选择笔记」下拉框中选取一篇笔记，或在「或输入文本」中粘贴要分析的内容（字数上限以输入框提示为准）。',
          '点击「开始分析」或等价按钮启动任务。',
          '右侧「分析结果」区域展示输出；需要时可使用复制等功能带走文本。'
        ]
      }
    ]
  },
  {
    id: 'manual-feature-tr',
    title: '翻译笔记',
    routeHint: '/ai/translate',
    paragraphs: [
      '在三栏布局中载入原文、选择目标语言并发起翻译；右侧以 **Markdown 流式** 显示译文（富文本 HTML 会在服务端先转为 Markdown 再翻译，避免截断在标签中间）。页面会提示超长截断与水印说明。'
    ],
    sections: [
      {
        title: '原文',
        items: [
          '可通过「上传文件」选择 .md / .txt 等（具体以后缀过滤为准）；或从「从我的笔记选择」下拉框选取一篇已有笔记。',
          '可在折叠面板「编辑原文」中直接粘贴或修改将要提交的文本。',
          '中间预览区展示将要发送的原文渲染效果（富文本 / Markdown 预览说明见页眉）。'
        ]
      },
      {
        title: '翻译与结果',
        items: [
          '在中间「翻译为」处选择目标语言。',
          '若正文过长，页面可能出现截断提示；请按提示缩短或分段。',
          '点击「开始翻译」后译文会逐字出现；完成后可复制全文。译文以 Markdown 渲染，可能带有「笔记助手」水印或脚注类标识。',
          '在支持的页面之间切换时，表单状态可能被保留；强刷或关闭标签页可能导致未保存内容丢失。'
        ]
      }
    ]
  },
  {
    id: 'manual-feature-mind',
    title: '思维导图',
    routeHint: '/mindmap',
    paragraphs: [
      '通过顶部导航「思维导图」进入独立页面，用于查看或整理导图相关内容；若首页 AI 回复中包含可识别的导图结构，也可能提供跳转到本页预览的按钮（以实际界面为准）。'
    ],
    sections: []
  },
  {
    id: 'manual-feature-user',
    title: '个人中心',
    routeHint: '/user',
    paragraphs: [
      '管理头像、邮箱展示、注册时间与密码安全；查看笔记与 AI 使用概况；可选配置自带模型（详见本手册「AI 与自带模型」）。'
    ],
    sections: [
      {
        title: '常用区块',
        items: [
          '个人信息：展开后更换头像、查看基本资料。',
          '数据统计：展开后查看笔记数、AI 使用次数、活跃天数等。',
          '安全设置：修改登录密码。',
          'AI 模型（自带密钥）：填写或更新自带推理接口（可选）。'
        ]
      }
    ]
  }
]

const featureChildIds = new Set(FEATURE_ITEMS.map((f) => f.id))

const tocTree = [
  { id: 'manual-intro', label: '项目介绍' },
  { id: 'manual-terms', label: '用户协议' },
  { id: 'manual-privacy', label: '隐私说明' },
  { id: 'manual-account', label: '账号与个人资料' },
  { id: 'manual-ai-byok', label: 'AI 与自带模型' },
  {
    id: 'manual-features',
    label: '功能说明',
    children: FEATURE_ITEMS.map(({ id, title }) => ({ id, label: title }))
  },
  { id: 'manual-faq', label: '常见问题' },
  { id: 'manual-feedback', label: '反馈与缺陷报告' },
  { id: 'manual-more', label: '关于本文档' }
]

const folderIds = tocTree.filter((n) => n.children?.length).map((n) => n.id)

const tocCollapsed = ref(false)
const expandedKeys = ref(new Set(folderIds))
const activeSectionId = ref('manual-intro')
const docBodyRef = ref(null)

const activeFeatureItem = computed(() => FEATURE_ITEMS.find((f) => f.id === activeSectionId.value) ?? null)

function isExpanded(id) {
  return expandedKeys.value.has(id)
}

function toggleExpand(id) {
  const next = new Set(expandedKeys.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  expandedKeys.value = next
}

function isNodeActive(nodeId) {
  if (activeSectionId.value === nodeId) {
    return true
  }
  if (nodeId === 'manual-features' && featureChildIds.has(activeSectionId.value)) {
    return true
  }
  return false
}

function selectSection(id) {
  activeSectionId.value = id
  if (id.startsWith('manual-feature-') && id !== 'manual-features') {
    const next = new Set(expandedKeys.value)
    next.add('manual-features')
    expandedKeys.value = next
  }
  nextTick(() => {
    const el = docBodyRef.value
    if (el) {
      el.scrollTop = 0
    }
  })
}
</script>

<style scoped>
.manual-page {
  padding: 16px 20px 48px;
  box-sizing: border-box;
}

.manual-split {
  display: flex;
  align-items: stretch;
  gap: 24px;
  max-width: 1120px;
  margin: 0 auto;
}

.manual-toc {
  flex: 0 0 236px;
  width: 236px;
  min-height: 0;
  transition: flex-basis 0.22s ease, width 0.22s ease;
}

.manual-split--collapsed .manual-toc {
  flex-basis: 56px;
  width: 56px;
}

.manual-toc-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  background: #f9fafb;
  border: 1px solid #ebeef5;
  border-radius: 10px;
}

.manual-split--collapsed .manual-toc-inner {
  padding: 10px 8px;
  align-items: center;
}

.manual-toc-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
  margin-bottom: 10px;
}

.manual-split--collapsed .manual-toc-toolbar {
  flex-direction: column;
  margin-bottom: 8px;
  width: 100%;
}

.manual-toc-title {
  font-size: 13px;
  font-weight: 600;
  color: #909399;
  letter-spacing: 0.02em;
}

.manual-toc-toggle {
  flex-shrink: 0;
}

.manual-toc-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: 2px;
}

.toc-tree {
  font-size: 13px;
  line-height: 1.45;
  user-select: none;
}

.toc-tree-root + .toc-tree-root {
  margin-top: 2px;
}

.toc-row {
  display: flex;
  align-items: flex-start;
  gap: 2px;
  border-radius: 4px;
  padding: 2px 0;
}

.toc-row:hover {
  background: rgba(64, 158, 255, 0.06);
}

.toc-caret-btn {
  flex: 0 0 22px;
  width: 22px;
  height: 22px;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.toc-caret-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #606266;
}

.toc-caret {
  font-size: 14px;
  transition: transform 0.15s ease;
}

.toc-caret--open {
  transform: rotate(90deg);
}

.toc-leaf-slot {
  flex: 0 0 22px;
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.toc-link {
  flex: 1;
  min-width: 0;
  padding: 1px 4px 1px 0;
  color: #606266;
  text-decoration: none;
  cursor: pointer;
  text-align: left;
  border: none;
  background: transparent;
  font: inherit;
  border-radius: 4px;
}

.toc-link:hover {
  color: #409eff;
}

.toc-link--active {
  color: #409eff;
  font-weight: 600;
  background: rgba(64, 158, 255, 0.12);
}

.toc-link--child {
  font-size: 12px;
  color: #606266;
}

.toc-link--child.toc-link--active {
  font-size: 12px;
}

.toc-tree-children {
  margin: 2px 0 4px 10px;
  padding: 2px 0 2px 10px;
  border-left: 1px solid #dcdfe6;
}

.toc-row--child {
  padding-left: 0;
}

.manual-toc-collapsed-hit {
  flex: 1;
  min-height: 120px;
  width: 100%;
  margin: 0;
  padding: 8px 0;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  color: #909399;
  font-size: 13px;
  font-family: inherit;
}

.manual-toc-collapsed-hit:hover {
  background: rgba(64, 158, 255, 0.08);
  color: #409eff;
}

.manual-toc-collapsed-text {
  display: block;
  writing-mode: vertical-rl;
  letter-spacing: 0.2em;
  margin: 0 auto;
}

.manual-doc {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.manual-doc-body {
  flex: 1;
  min-height: min(70vh, 640px);
  overflow-y: auto;
  padding: 20px 22px 28px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  box-sizing: border-box;
}

.manual-doc-pane {
  min-height: 0;
}

.manual-block {
  max-width: 720px;
}

.manual-intro-block h1 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}

.manual-lead {
  margin: 0 0 16px;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.manual-tip {
  margin-bottom: 16px;
}

.manual-tip + .manual-h3 {
  margin-top: 8px;
}

.manual-block h2 {
  margin: 0 0 12px;
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.manual-footer-title {
  margin: 0 0 10px;
  font-size: 17px;
  font-weight: 600;
  color: #303133;
}

.manual-h3 {
  margin: 20px 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.manual-h3:first-of-type {
  margin-top: 12px;
}

.manual-intro-block .manual-h3:first-of-type {
  margin-top: 20px;
}

.manual-crumb {
  margin: 0 0 10px;
  font-size: 12px;
  color: #909399;
  letter-spacing: 0.02em;
}

.manual-route-hint {
  margin: -4px 0 12px;
  font-size: 13px;
  color: #909399;
}

.manual-route-hint code {
  font-size: 12px;
}

.manual-list {
  margin: 8px 0 0;
  padding-left: 20px;
  font-size: 14px;
  color: #606266;
  line-height: 1.65;
}

.manual-list--compact li {
  margin-bottom: 4px;
}

.manual-list li {
  margin-bottom: 8px;
}

.manual-list code {
  font-size: 12px;
  padding: 1px 6px;
  background: #f5f7fa;
  border-radius: 4px;
}

.manual-p {
  margin: 0 0 8px;
  font-size: 14px;
  color: #606266;
  line-height: 1.65;
}

.manual-p--tight {
  margin-bottom: 0;
  margin-top: 8px;
}

.manual-muted {
  margin: 12px 0 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}

.manual-mail-block {
  margin: 8px 0 0;
}

.manual-mailto {
  font-size: 15px;
  font-weight: 600;
  color: #409eff;
  word-break: break-all;
}

.manual-inline-link {
  color: #409eff;
  word-break: break-all;
}

.manual-footer {
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}

.manual-footer .manual-p {
  color: #606266;
}

@media (max-width: 900px) {
  .manual-split {
    flex-direction: column;
    gap: 16px;
  }

  .manual-split--collapsed .manual-toc {
    flex-basis: auto;
    width: 100%;
  }

  .manual-toc {
    flex: none;
    width: 100%;
  }

  .manual-split--collapsed .manual-toc-inner {
    flex-direction: row;
    align-items: flex-start;
    padding: 10px 12px;
  }

  .manual-split--collapsed .manual-toc-toolbar {
    flex-direction: row;
    margin-bottom: 0;
    width: auto;
  }

  .manual-toc-collapsed-hit {
    flex: none;
    min-height: auto;
    width: auto;
    padding: 4px 12px;
  }

  .manual-toc-collapsed-text {
    writing-mode: horizontal-tb;
    letter-spacing: normal;
  }

  .manual-doc-body {
    min-height: 360px;
  }
}
</style>
