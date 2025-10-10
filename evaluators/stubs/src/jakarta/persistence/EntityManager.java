package jakarta.persistence;

public interface EntityManager {
    void persist(Object entity);
    <T> T merge(T entity);
    void remove(Object entity);
    <T> T find(Class<T> entityClass, Object primaryKey);
    void flush();
    void close();
}
