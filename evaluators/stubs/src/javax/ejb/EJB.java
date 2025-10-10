package javax.ejb;

import java.lang.annotation.*;

@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
public @interface EJB {
    String name() default "";
    String beanName() default "";
    Class beanInterface() default Object.class;
    String mappedName() default "";
    String description() default "";
}
