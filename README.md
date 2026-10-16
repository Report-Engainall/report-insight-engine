# Report Insight Engine

هذا المشروع: https://github.com/Report-Engainall/Report-Advisor
زيد اتاكد لي شهرين وانا اشتغل على هذا المشروع يعني ان هناك اشياء كثيرة من القلب والعقل موجودة فحاول ان تتاكد وتستورد كل ما يفيد احنا ويختصر علينا الوقت ولا تنسى شئ

طبعا يا سيدي المشروع اريدة يحلل اي ملف تقارير ايا كان ويطلع كل التقارير الذكية عنة والاستشارية والارشادية والتحذيرية وحت انة يضع مهام للموضفين كلا بحسب تخصصة ويحدد مهامة اليومية ويوضع التوصيات وايش وماذا ولماذا وكيف وماذا لو الخ الخ كل المواصفات مرسلة لك سابقا واريد كل ذالك بدون استخدام اي ادوات مدفوعة.
واريد منك ان تضع افضل شاشات بصرية مترابطة وذكية تبهر المستخدم من اول الاستخدام.
علما اني لا اريد 48 تقرير هم فقط كنماذج للتجربة فقط بينما المطلوب هو التنفيذ على اي تقرير كان.
انطلق وستخدم كل الاشياء الموجودة وطورها واصلحها والغير موجود انشئه وحتفظ بالمشروع للمرة الجاية ونقطة التوقف ايضا لتواصل من حيث توقفت.

المرفقان: ملف الجرد (لكل ملف قرار الاستيراد keep / keep-reference / keep-doc / review / skip مع السبب) وملف التحقق من القدرات (ما هو موجود، وما هو جزئي، وما هو مفقود). راجعهما وعدّلهما بعد فحصك.

قيد إلزامي — التطبيق بدون أدوات أو خدمات مدفوعة: يجب أن يكون المنتج الأساسي قابلاً للتشغيل بدون اشتراك في خدمة مدفوعة خارجية، وأي dependency جديدة يجب توثيق PURPOSE, LICENSE, COST, SELF-HOST OPTION, FALLBACK, WHY REQUIRED.

قاعدة كل تقرير: لا تحصر الذكاء في الـ48 Archetypes. كل ملف تقرير يُرفع (معروف أو مجهول) يمر عبر: UPLOAD → DISCOVER → PARSE → NORMALIZE → SEMANTIC MAP → PROFILE → DATA QUALITY → TRUTH → DETECT APPLICABLE INTELLIGENCE → RUN ALL VALID CAPABILITIES → EXPLAIN → ADVISE → DECIDE → APPROVAL → WORK → OUTCOME → LEARNING → READBACK → DISPLAY.
الـ48 Archetypes مسرّعات متخصصة فقط وليست حداً للمنتج. UNKNOWN REPORT لا يعني LIMITED REPORT.

الفحص: كل قدرة (CORE METRICS, QUALITY, TRENDS, COMPARISONS, CONCENTRATION, SEGMENTATION, DEPENDENCY, DISTRIBUTION, OUTLIERS, ANOMALIES, CHANGE POINTS, DRIVERS, RISKS, OPPORTUNITIES, BUSINESS QUESTIONS, CROSS-SOURCE RECONCILIATION, FORECAST, UNCERTAINTY, SENSITIVITY, WHAT-IF, COUNTERFACTUAL, CAUSAL ANALYSIS, OPTIMIZATION, VOI, PROCESS INTELLIGENCE, KNOWLEDGE GRAPH, CROSS-DOMAIN REASONING, DECISION PORTFOLIO, DECISION REPLAY, ACTIVE LEARNING, BENCHMARK, ROW/CELL PROVENANCE) تُفحص قابليتها أولاً وتُشغَّل إن توفرت مدخلاتها. حالتها: AVAILABLE / NOT_AVAILABLE / INSUFFICIENT_SAMPLE / REVIEW_REQUIRED / BLOCKED، ومعها WHY, REQUIRED INPUTS, AVAILABLE INPUTS, MISSING INPUTS, EVIDENCE, ASSUMPTIONS, LIMITATIONS, PROVENANCE.
ممنوع: تحويل الارتباط إلى سببية، أو اختلاق توقع أو أثر مالي أو benchmark أو confidence بدون متطلبات كافية. لا silent failure ولا parallel engines.

العرض: WHAT → WHY → SO WHAT → IMPACT → WHAT NEXT → PROOF، مع OWNER و EXPECTED OUTCOME عندما تسمح الأدلة.
الإنجاز الحقيقي: كل قدرة قابلة للتطبيق تصل إلى IMPLEMENTED → ORCHESTRATED → EXECUTED ON REAL DATA → PERSISTED → READ BACK → RENDERED → BROWSER PROVEN. اختبر بتقرير حقيقي مجهول النوع (يمكن استخدام tests/fixtures/realistic-reports) وأظهر الحفظ والاسترجاع.

الواجهة: بأحدث المزايا البصرية، مع RTL عربي.
لا تعيد بناء المحركات الموجودة ولا تحذفها. ابدأ بفحص الحالة الفعلية (HEAD, runtime, database, import, smart report, UI, tests, production)، ثم أغلق أول P0/P1 حقيقي.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/db30fa09-5d6d-48ee-8806-264ae7319d03).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
