import math
import random
import sys
import time

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex04/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.hyper_life = -1
        self.state = "normal"

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex04/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)


    # 状態変化メソッド
    def change_state(self, state: str, hyper_life: int):
        """
        状態変化メソッド
        引数1 状態
        引数2 発動時間
        """
        self.state = state
        self.hyper_life = hyper_life
        # self.image = pg.transform.laplacian(self.image)
        # if self.state == "hyper" and hyper_life < 0:
        #     self.change_state()


    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        if self.state == "hyper":
            self.hyper_life -= 1
            # print(self.hyper_life) # デバッグ用
            self.image = pg.transform.laplacian(self.image)
        if self.hyper_life < 0:
            self.change_state("normal", -1)
        screen.blit(self.image, self.rect)
    
    def get_direction(self) -> tuple[int, int]:
        return self.dire
    

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, rot_angle=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + rot_angle
        self.image = pg.transform.rotozoom(pg.image.load(f"ex04/fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class NeoBeam(pg.sprite.Sprite):
    """
    一度に複数方向へビームを発射させる
    """
    def __init__(self, bird: Bird, num: int):
        self.beams = list()
        self.bird = bird
        self.num = num

    def gen_beams(self) -> list[Beam]:
        vx, vy = self.bird.get_direction()
        for angle in range(-50, +51, int(100/(self.num-1))):
            self.beams.append(Beam(self.bird, angle))
        return self.beams

      
class NeoGravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    """
    def __init__(self, life: int):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT), flags=pg.SRCALPHA)
        self.image.fill((0,0,0,120))
        self.rect = self.image.get_rect()
        self.life = life

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()
        

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex04/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex04/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)

#future5
class Shield(pg.sprite.Sprite):
    def __init__(self, bird, life):
        super().__init__()
        self.image = pg.Surface((20, bird.rect.height * 2))
        self.image.fill((0, 0, 0))  # 黒い矩形
        self.rect = self.image.get_rect()

        # 防御壁の位置をこうかとんの前に設定
        direction = bird.get_direction()
        if direction == (1, 0):
            self.rect.topleft = (bird.rect.right, bird.rect.centery - bird.rect.height)
        elif direction == (-1, 0):
            self.rect.topleft = (bird.rect.left - 20, bird.rect.centery - bird.rect.height)
        elif direction == (0, 1):
            self.rect.topleft = (bird.rect.centerx - 10, bird.rect.bottom)
        elif direction == (0, -1):
            self.rect.topleft = (bird.rect.centerx - 10, bird.rect.top - bird.rect.height * 2)
        self.life = life

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()

        
        
        

class Gravity(pg.sprite.Sprite):
    """
    重力球に関するクラス
    """
    def __init__(self, bird: Bird, size: int, life: int):
        """
        重力球Surfaceを生成する
        引数1 bird: 重力球の座標参考になるこうかとん
        引数2 size: 重力球の大きさ
        引数3 life: 重力球の発動時間
        """
        super().__init__() # spriteクラスのイニシャライザを呼び出す
        
        self.image = pg.Surface((2*size, 2*size))
        self.image.set_alpha(200) # 重力球を半透明にする
        self.image.set_colorkey((0, 0, 0))
        pg.draw.circle(self.image, (10, 10, 10), (size, size), size)
        
        self.rect = self.image.get_rect(center=bird.rect.center) # 座標をこうかとんに貼り付けるイメージ
        self.life = life
  
    
    def update(self):
        """"
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        制限時間が来たら重量球を解除
        引数 screen：画面Surface
        """
        self.life -= 1
        if self.life < 0:
            self.kill()
        

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex04/fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()


    tmr = 0
    power_score = 100 # 肉体強化に必要なスコア

    #future5
    shields = pg.sprite.Group()
    shield_active = False  # 防御壁がアクティブかどうか

    gravity = pg.sprite.Group()
    gravs = pg.sprite.Group()


    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(NeoBeam(bird, 5).gen_beams())
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                bird.speed = 20
            else:
                bird.speed = 10
                          
            # 肉体強化
            if event.type == pg.KEYDOWN \
                and event.key == pg.K_RSHIFT\
                and score.score >= power_score: # スコアが100以上なら
                # 呼び出し
                bird.change_state("hyper", 500)
                score.score -= power_score
                          
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and score.score >= 10:
                score.score -= 10
                gravity.add(NeoGravity(10))

            if event.type == pg.KEYDOWN and event.key ==  pg.K_TAB: # TABキーが押されたら重力球
                # スコア50消費して重力球を生成
                if score.score >= 10:
                    gravs.add(Gravity(bird, 200, 500)) # (bird, 半径, 発動時間)
                    score.score -= 10

        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))



        # 敵にビームが当たったときの処理
        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
                          
        # 爆弾にビームが当たったときの処理
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            if bird.state == "normal":
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            elif bird.state == "hyper":
                exps.add(Explosion(bird, 50))  # 爆発エフェクト
                score.score_up(1)  # 1点アップ
                score.update(screen)
                pg.display.update()
                          
        for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
        
        # 爆弾に重力球があたったときも処理
        for bomb in pg.sprite.groupcollide(bombs, gravs, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ


        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        #future5
        if key_lst[pg.K_a] and score.score >= 50 and not shield_active:
            # Aキーが押され、スコアが50以上で、防御壁がアクティブでない場合
            shields.add(Shield(bird, 400))  # 防御壁を発動
            shield_active = True
            score.score_up(-50)  # スコアを減少させる
        
        # 防御壁と爆弾の衝突を検出し、爆弾を破壊
        for shield in pg.sprite.groupcollide(shields, bombs, False, True).keys():
            exps.add(Explosion(shield, 50))  # 防御壁の爆発エフェクト
            score.score_up(1)  # スコアを増加
            shield.kill()  # 防御壁を削除
            shield_active = False  # 防御壁の寿命が尽きたら非アクティブにする

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)

        #future5
        shields.update()
        shields.draw(screen)

        gravity.update()
        gravity.draw(screen)
        gravs.update()
        gravs.draw(screen)

        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)
        
if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
