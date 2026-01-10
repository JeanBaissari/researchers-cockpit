# 📋 PULL REQUEST - DENDRA EVENTOS

## Description

Brief technical description in English (for developer audience)

**Note:** UI text must remain 100% Spanish - this requirement is for PR documentation only.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Style/UI update
- [ ] ♻️ Code refactor
- [ ] ⚡ Performance improvement

## Affected Areas

- [ ] Frontend (Customer-facing)
- [ ] Admin Panel
- [ ] API Routes
- [ ] Database/Prisma
- [ ] Authentication
- [ ] Payment Integration (MercadoPago)
- [ ] Cart System
- [ ] Documentation

## Dendra-Specific Checklist ⚠️

- [ ] **Spanish translations** complete (all UI text in Spanish)
- [ ] **Mobile tested** (responsive design works on mobile devices)
- [ ] **Brand colors** used exclusively (dark-teal, teal, coral, cream)
- [ ] **Cursor rules** followed (check relevant `.cursor/rules/*.mdc` files)
- [ ] **Rule files updated** (if new patterns introduced)

**Note:** "Spanish translations complete" refers to user-facing UI text only. PR descriptions should be in English for technical clarity and searchability.

## Testing Checklist

- [ ] Code compiles without errors (`npm run build`)
- [ ] TypeScript strict mode passes (NO `any` types)
- [ ] All Prisma queries have error handling
- [ ] Tested on mobile devices (iOS/Android)
- [ ] Tested on desktop browsers (Chrome, Firefox, Safari)
- [ ] Loading states implemented
- [ ] Error states handled (with Spanish messages)
- [ ] Empty states included (where applicable)

## Database Changes

- [ ] No database changes
- [ ] Migration created and tested (`npx prisma migrate dev`)
- [ ] Seed data updated if needed
- [ ] Row-Level Security (RLS) policies reviewed
- [ ] Breaking changes documented in FAQ.md

## Screenshots (if UI changes)

<!-- Add screenshots showing desktop AND mobile views -->
<!-- Delete this section if no UI changes -->

## Pre-Deployment Checklist

- [ ] Environment variables documented (in README or FAQ)
- [ ] NO console.logs in production code
- [ ] API routes have authentication checks (NextAuth)
- [ ] Forms have client AND server validation (Zod)
- [ ] Images use Next.js Image component
- [ ] Tailwind classes use brand colors ONLY
- [ ] No hardcoded prices/dates (use database)
- [ ] Spanish error messages for all user-facing errors

## Related Issues

Closes #(issue number)

## Additional Notes

<!-- Any additional context, decisions, or trade-offs for reviewers -->

## Code Review Focus Areas

Please pay special attention to:

- [ ] Security implications (auth, data exposure)
- [ ] Performance impact (N+1 queries, bundle size)
- [ ] Database query efficiency (includes, transactions)
- [ ] Type safety (explicit types, no assertions)
- [ ] Error handling (try-catch, user-friendly messages)

---

## Reviewer Checklist

**Reviewers**: Verify these before approving

### Code Standards

- [ ] Follows `.cursor/rules/` standards for affected domains
- [ ] No hardcoded values (use env variables or database)
- [ ] Component follows atomic design pattern
- [ ] Git commit messages follow convention (`type(scope): subject`)
- [ ] File organization follows project structure

### Dendra Standards

- [ ] All UI text in Spanish (including buttons, labels, errors)
- [ ] Brand colors used (NO arbitrary colors like `bg-red-500`)
- [ ] Mobile-first responsive design
- [ ] Loading skeletons for async content
- [ ] Error boundaries where appropriate

### Documentation

- [ ] Documentation updated if needed (README, FAQ, memorybank)
- [ ] New patterns documented in appropriate rule files
- [ ] Breaking changes clearly documented
- [ ] Migration instructions provided (if applicable)

---

**Deployment**: After approval, this will auto-deploy to Vercel preview → Production (if merged to main)
