package javax.ejb;

import java.lang.annotation.*;

@Target({ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface MessageDriven {
    ActivationConfigProperty[] activationConfig() default {};
    String name() default "";
    String mappedName() default "";
}
