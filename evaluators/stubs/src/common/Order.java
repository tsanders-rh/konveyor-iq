// Common domain object stub
public class Order {
    private Long id;
    private User user;

    public Order() {}

    public Order(User user) {
        this.user = user;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
}
