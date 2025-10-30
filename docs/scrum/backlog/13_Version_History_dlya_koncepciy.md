### #13 - Version History для концепций

**User Story:**
Как пользователь, я хочу видеть историю изменений концепции, чтобы откатиться к предыдущей версии.

**Acceptance Criteria:**
- [ ] Модель ConceptVersion (snapshot при каждом update)
- [ ] GraphQL query: conceptVersions(conceptId: Int!)
- [ ] Diff между версиями
- [ ] Restore previous version
- [ ] Blame (кто и когда изменил)

**Estimated Effort:** 8 story points

**Status:** 📋 Backlog