# Course UI components

These components share the MOA Academy layout and the --brand color token. They handle presentation and emit actions so views can connect them to the course API, router, and payment flow.

Example:

    import { CourseGrid, CoursePageLayout, CourseSearchBar } from '@/components'

    <CoursePageLayout active-page="catalog">
      <CourseSearchBar :categories="['Development', 'Design']" @search="loadCourses" />
      <CourseGrid :courses="courses" @select="openCourse" />
    </CoursePageLayout>

| Component | Main inputs | Events |
| --- | --- | --- |
| CoursePageLayout | activePage (catalog, detail, auth) | default slot |
| CourseSearchBar | keyword, category, categories | search, update:keyword, update:category |
| CourseCard | course, saved | select, toggle-save |
| CourseGrid | courses, title, savedIds, emptyMessage; optional actions slot | select, toggle-save |
| CourseSummary | title, category, instructor, summary | share, save |
| CourseGallery | images ({ src, alt }[]), title | select-image |
| CoursePurchaseCard | price, purchasing, purchased, disabled | purchase |
| CourseAuthDialog | modelValue, initialMode, loading, error, notice | update:modelValue, submit, social-login, switch-mode |

Course objects use id, title, category, instructor_name, summary, thumbnail_url, and price_krw.
