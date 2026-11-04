package app.flexygram.motionbuild;

import java.util.function.BiPredicate;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;

/** Rewrite typed presentation entry points; no reflection, framework patches or timer rewrites. */
public final class FastMotionVisitor extends ClassVisitor {
    private static final String RUNTIME="app/flexygram/animation/FastMotion";
    private final BiPredicate<String,String> inherits;
    public FastMotionVisitor(ClassVisitor next,BiPredicate<String,String> inherits) {
        super(Opcodes.ASM9,next);this.inherits=inherits;
    }
    @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions) {
        return new MethodVisitor(Opcodes.ASM9,super.visitMethod(access,name,descriptor,signature,exceptions)) {
            @Override public void visitMethodInsn(int opcode,String owner,String name,String desc,boolean iface) {
                // Super calls must retain invokespecial: wrapping them would recurse through overrides.
                if (opcode==Opcodes.INVOKEVIRTUAL) {
                    if(name.equals("start") && desc.equals("()V")) {
                        if(inherits.test(owner,"android.animation.Animator")) {
                            call("start","(Landroid/animation/Animator;)V");return;
                        }
                        if(owner.equals("android/view/ViewPropertyAnimator")) {
                            call("start","(Landroid/view/ViewPropertyAnimator;)V");return;
                        }
                        if(inherits.test(owner,"androidx.dynamicanimation.animation.DynamicAnimation")) {
                            call("startSpring","(Landroidx/dynamicanimation/animation/DynamicAnimation;)V");return;
                        }
                    }
                    if(owner.equals("android/view/ViewPropertyAnimator") && desc.equals("(J)Landroid/view/ViewPropertyAnimator;")) {
                        if(name.equals("setDuration")){call("duration","(Landroid/view/ViewPropertyAnimator;J)Landroid/view/ViewPropertyAnimator;");return;}
                        if(name.equals("setStartDelay")){call("delay","(Landroid/view/ViewPropertyAnimator;J)Landroid/view/ViewPropertyAnimator;");return;}
                    }
                    if(name.equals("startAnimation") && desc.equals("(Landroid/view/animation/Animation;)V") && inherits.test(owner,"android.view.View")) {
                        call("startAnimation","(Landroid/view/View;Landroid/view/animation/Animation;)V");return;
                    }
                    if(name.equals("animate") && desc.equals("()Landroid/view/ViewPropertyAnimator;") && inherits.test(owner,"android.view.View")) {
                        super.visitMethodInsn(opcode,owner,name,desc,iface);
                        call("viewAnimator","(Landroid/view/ViewPropertyAnimator;)Landroid/view/ViewPropertyAnimator;");return;
                    }
                }
                super.visitMethodInsn(opcode,owner,name,desc,iface);
            }
            private void call(String name,String desc){super.visitMethodInsn(Opcodes.INVOKESTATIC,RUNTIME,name,desc,false);}
        };
    }
}
