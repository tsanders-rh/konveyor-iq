#!/usr/bin/env python3
"""
Test script to validate stub generation logic.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from generate_tests import TestCaseGenerator

def test_jpa_entity_detection():
    """Test detection and stub generation for JPA entities."""
    print("=" * 70)
    print("Test 1: JPA Entity with @ManyToOne relationship")
    print("=" * 70)

    code_snippet = """
import javax.persistence.*;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "customer_id")
    private CustomerEntity customer;

    private String orderNumber;
}
"""

    expected_fix = """
import jakarta.persistence.*;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "customer_id")
    private CustomerEntity customer;

    private String orderNumber;
}
"""

    generator = TestCaseGenerator()
    stubs = generator._generate_test_stubs(code_snippet, expected_fix)

    print("\nGenerated Stubs:")
    print(stubs)
    print()


def test_repository_pattern():
    """Test detection and stub generation for repository pattern."""
    print("=" * 70)
    print("Test 2: Service class with Repository injection")
    print("=" * 70)

    code_snippet = """
import javax.ejb.Stateless;
import javax.inject.Inject;

@Stateless
public class OrderService {
    @Inject
    private OrderRepository orderRepository;

    public void processOrder(OrderEntity order) {
        orderRepository.save(order);
    }
}
"""

    expected_fix = """
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class OrderService {
    @Inject
    private OrderRepository orderRepository;

    public void processOrder(OrderEntity order) {
        orderRepository.save(order);
    }
}
"""

    generator = TestCaseGenerator()
    stubs = generator._generate_test_stubs(code_snippet, expected_fix)

    print("\nGenerated Stubs:")
    print(stubs)
    print()


def test_dto_pattern():
    """Test detection and stub generation for DTO pattern."""
    print("=" * 70)
    print("Test 3: Service returning DTO")
    print("=" * 70)

    code_snippet = """
import javax.ejb.Stateless;

@Stateless
public class CustomerService {
    public CustomerDTO getCustomerInfo(Long id) {
        CustomerDTO dto = new CustomerDTO();
        dto.setId(id);
        return dto;
    }
}
"""

    expected_fix = """
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class CustomerService {
    public CustomerDTO getCustomerInfo(Long id) {
        CustomerDTO dto = new CustomerDTO();
        dto.setId(id);
        return dto;
    }
}
"""

    generator = TestCaseGenerator()
    stubs = generator._generate_test_stubs(code_snippet, expected_fix)

    print("\nGenerated Stubs:")
    print(stubs)
    print()


def test_no_external_deps():
    """Test that no stubs are generated for self-contained code."""
    print("=" * 70)
    print("Test 4: Self-contained class (no external dependencies)")
    print("=" * 70)

    code_snippet = """
import javax.ejb.Stateless;

@Stateless
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""

    expected_fix = """
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
"""

    generator = TestCaseGenerator()
    stubs = generator._generate_test_stubs(code_snippet, expected_fix)

    if stubs:
        print("\nGenerated Stubs:")
        print(stubs)
    else:
        print("\n✓ No stubs generated (as expected for self-contained code)")
    print()


def test_class_detection():
    """Test the _detect_referenced_classes method."""
    print("=" * 70)
    print("Test 5: Class detection logic")
    print("=" * 70)

    code = """
    @Inject
    private CustomerRepository customerRepo;

    private OrderEntity order;

    public CustomerDTO processCustomer(OrderDTO orderDto) {
        return new CustomerDTO();
    }
    """

    generator = TestCaseGenerator()
    detected = generator._detect_referenced_classes(code)

    print(f"\nDetected classes: {detected}")
    print()


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("STUB GENERATION TEST SUITE")
    print("=" * 70 + "\n")

    test_class_detection()
    test_jpa_entity_detection()
    test_repository_pattern()
    test_dto_pattern()
    test_no_external_deps()

    print("=" * 70)
    print("All tests completed!")
    print("=" * 70)
