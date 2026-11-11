---
name: invoice-app-map
description: Maps the Invoice Approval demo to Spring Boot equivalents and states the invoice lifecycle. Use when explaining, changing, or reviewing this .NET codebase, especially for someone who knows Java and Spring Boot, or when asked how invoices, auth, or persistence work.
---

# Invoice app map

This repository is an ASP.NET Core 8 web API plus a static UI. Business rules live in `InvoiceApp.Domain`. The host, controllers, sign-in, and in-memory store live in `InvoiceApp.Api`.

## Spring Boot equivalents

- `InvoiceApp.Api` is the Spring Boot application. `Program.cs` is `main` plus bean registration.
- Controllers are REST controllers. Request bodies are C# `record` types, the same idea as Java records.
- `ApiControllerBase.Handle` maps exceptions the way a small `@ControllerAdvice` would: `KeyNotFoundException` is 404, `InvalidOperationException` is 409, `ArgumentException` is 400.
- `SessionAuthMiddleware` is a servlet filter. Every `/api` call except `POST /api/auth/login` requires `Authorization: Bearer <token>`.
- `RequireRole` is `@PreAuthorize`. Approve and reject require Approver or Admin. Delete requires Admin. Create and submit require only a signed-in user.
- `ApprovalService` is the domain service. `IInvoiceRepository` is the repository interface. `InMemoryInvoiceRepository` is a process-local list, registered as a singleton in `Program.cs`.
- `wwwroot/` is static content, like `src/main/resources/static`. The browser stores the token in `sessionStorage`.
- xUnit `[Fact]` methods are JUnit tests. `FakeInvoiceRepository` is the test double.

## Lifecycle

`ApprovalService` is the only type that changes invoice status.

- Create stores a `Draft`.
- `Submit` accepts only `Draft` and moves it to `PendingApproval`.
- `Approve` and `Reject` accept only `PendingApproval`. Reject requires a non-blank reason. Both stamp `DecidedBy` and `DecidedAt`.
- There is no payment call after approval.

`DiscountCalculator` is in Domain and is not called by a controller, by `ApprovalService`, or by a test. `IInvoiceRepository.GetByIds` is implemented and has no production caller.

## Planned deployment is not the code

`ops/` describes a future production shape: Azure SQL, Azure Service Bus, and PayEx. None of those exist in the code. Do not describe them as part of the running system. Demo users in `appsettings.json` are local demo accounts, not production credentials.
