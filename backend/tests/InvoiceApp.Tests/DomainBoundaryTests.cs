using InvoiceApp.Domain;
using Xunit;

namespace InvoiceApp.Tests;

public class DomainBoundaryTests
{
    [Fact]
    public void DomainAssemblyDoesNotReferenceTheWebHost()
    {
        var referencedNames = typeof(ApprovalService).Assembly
            .GetReferencedAssemblies()
            .Select(assembly => assembly.Name)
            .Where(name => name is not null)
            .Cast<string>()
            .ToList();

        Assert.DoesNotContain("InvoiceApp.Api", referencedNames);
        Assert.DoesNotContain(
            referencedNames,
            name => name.StartsWith("Microsoft.AspNetCore", StringComparison.Ordinal));
    }
}
